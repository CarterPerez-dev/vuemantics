"""
AI service for media analysis and embedding generation.
Integrates Google Gemini for multimodal understanding and
OpenAI for semantic embeddings. Handles both images and videos.
---
/backend/services/ai_service.py
"""

import asyncio
import io
import logging
from pathlib import Path
from uuid import UUID

import google.genai as genai  # noqa: PLR0402
from openai import AsyncOpenAI
from PIL import Image

from config import settings
from models import ProcessingStatus, Upload
from services import storage_service

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """
    Base exception for AI service errors.
    """

    pass


class GeminiError(AIServiceError):
    """
    Raised when Gemini API fails.
    """

    pass


class OpenAIError(AIServiceError):
    """
    Raised when OpenAI API fails.
    """

    pass


class AIService:
    """
    Handles AI processing for uploads using Gemini and OpenAI.

    Workflow:
    1. Analyze media with Gemini to get text description
    2. Generate embedding from description using OpenAI
    3. Update upload record with results
    """

    def __init__(self):
        """
        Initialize AI service with lazy client initialization.
        """
        self._gemini_client = None
        self._openai_client = None
        self._gemini_model = "gemini-2.0-flash"  # FOR MVP (2.5 pro for prod)
        self._embedding_model = settings.embedding_model

        logger.info("AI service initialized (clients will be created on demand)")

    def _ensure_gemini_client(self):
        """Lazy initialization of Gemini client."""
        if self._gemini_client is None:
            if not settings.gemini_api_key:
                raise GeminiError("Gemini API key not configured")
            self._gemini_client = genai.Client(api_key=settings.gemini_api_key)
        return self._gemini_client

    def _ensure_openai_client(self):
        """Lazy initialization of OpenAI client."""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise OpenAIError("OpenAI API key not configured")
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    async def analyze_media(self, upload_id: UUID) -> None:
        """
        Analyze media file and generate embeddings.

        Args:
            upload_id: Upload to process

        Updates upload record with:
        - gemini_summary: Text description
        - embedding: 1536-dimensional vector
        - processing_status: completed or failed
        """
        upload = await Upload.find_by_id(upload_id)
        if not upload:
            logger.error(f"Upload {upload_id} not found")
            return

        try:
            # Update status to analyzing
            await upload.update_status(ProcessingStatus.ANALYZING)
            logger.info(f"Starting AI analysis for upload {upload_id}")

            # Get file path
            file_path = settings.upload_path / upload.file_path

            # Analyze with Gemini based on file type
            if upload.file_type == "image":
                description = await self._analyze_image_with_gemini(file_path)
            else:  # video
                description = await self._analyze_video_with_gemini(
                    upload.user_id, upload_id, file_path
                )

            if not description:
                raise GeminiError("Gemini returned empty description")

            logger.info(
                f"Gemini analysis complete for {upload_id}: {len(description)} chars"
            )

            # Update status to embedding
            await upload.update_status(ProcessingStatus.EMBEDDING)

            # Generate embedding from description
            logger.info(f"Starting embedding generation for {upload_id}")
            embedding = await self._generate_embedding(description)
            logger.info(
                f"Generated embedding for {upload_id}: {len(embedding)} dimensions"
            )

            # Update upload with results
            logger.info(f"Updating database with analysis results for {upload_id}")
            await upload.update_analysis(
                gemini_summary=description, embedding=embedding
            )

            logger.info(f"AI processing completed for upload {upload_id}")

        except Exception as e:
            logger.error(f"AI processing failed for upload {upload_id}: {e}")
            await upload.update_status(
                ProcessingStatus.FAILED,
                error_message=f"AI processing failed: {str(e)[:500]}",
            )

    async def _analyze_image_with_gemini(self, image_path: Path) -> str:
        """
        Analyze image with Gemini.

        Args:
            image_path: Path to image file

        Returns:
            Text description of image content
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = f.read()

            prompt = """Analyze this image and provide a detailed description that would help someone find it through text search.

Include:
- Main subjects (people, animals, objects)
- Actions or activities
- Setting/location
- Mood or atmosphere
- Notable colors or visual elements
- Any text visible in the image

Be specific and descriptive, using natural language that someone might use to search for this image."""

            response = await self._call_gemini_async(
                prompt=prompt,
                image_data=image_data,
                mime_type=self._get_mime_type(image_path),
            )

            return response.strip()

        except Exception as e:
            logger.error(f"Gemini image analysis failed: {e}")
            raise GeminiError(f"Failed to analyze image: {e!s}") from e

    async def _analyze_video_with_gemini(
        self, user_id: UUID, upload_id: UUID, video_path: Path
    ) -> str:
        """
        Analyze video with Gemini using extracted frames.

        Args:
            user_id: User ID
            upload_id: Upload ID
            video_path: Path to video file

        Returns:
            Text description of video content
        """
        try:
            # Extract frames for analysis
            extension = video_path.suffix[1:]  # Remove dot
            frame_paths = await storage_service.extract_video_frames(
                user_id=user_id,
                upload_id=upload_id,
                extension=extension,
                max_frames=settings.max_video_frames,
            )

            if not frame_paths:
                raise GeminiError("No frames extracted from video")

            # Read frame data
            frames_data = []
            for frame_path in frame_paths[:5]:  # Use first 5 frames
                full_path = settings.upload_path / frame_path
                with open(full_path, "rb") as f:
                    frames_data.append(f.read())

            # Video description
            prompt = f"""Analyze these {len(frames_data)} frames from a video and provide a comprehensive description.

Include:
- Main subjects and their actions throughout the video
- Changes or progression between frames
- Setting/location
- Overall theme or story
- Any text or important visual elements
- Mood or atmosphere

Describe it as a cohesive video, not individual frames. Be specific and use natural language that someone might use to search for this video."""

            response = await self._call_gemini_async(
                prompt=prompt,
                image_data=frames_data[0],  # Use first frame as primary
                additional_context=f"Video with {len(frames_data)} sampled frames",
            )

            return response.strip()

        except Exception as e:
            logger.error(f"Gemini video analysis failed: {e}")
            raise GeminiError(f"Failed to analyze video: {e!s}") from e

    async def _call_gemini_async(
        self,
        prompt: str,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        additional_context: str | None = None,
    ) -> str:
        """
        Call Gemini API asynchronously.

        Args:
            prompt: Text prompt
            image_data: Image bytes
            mime_type: MIME type of image
            additional_context: Optional extra context

        Returns:
            Generated text response
        """
        try:
            # Prepare the content
            contents = [
                genai.types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt,
            ]

            if additional_context:
                contents.append(additional_context)

            # Use asyncio to run in executor since SDK might not be fully async
            loop = asyncio.get_event_loop()

            def call_gemini():
                return self._ensure_gemini_client().models.generate_content(
                    model=self._gemini_model, contents=contents
                )

            response = await loop.run_in_executor(None, call_gemini)

            if not response.text:
                raise GeminiError("Empty response from Gemini")

            return response.text

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise GeminiError(f"Gemini API error: {e!s}") from e

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector from text using OpenAI.

        Args:
            text: Text to embed (Gemini description)

        Returns:
            1536-dimensional embedding vector
        """
        try:
            # Truncate if too long (max ~8000 tokens)
            max_chars = 32000  # MAX
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
                logger.warning(f"Truncated text from {len(text)} to {max_chars} chars")

            # Call OpenAI embeddings API
            response = await self._ensure_openai_client().embeddings.create(
                input=text, model=self._embedding_model, encoding_format="float"
            )

            embedding = response.data[0].embedding

            if len(embedding) != settings.embedding_dimensions:
                raise OpenAIError(
                    f"Invalid embedding dimensions: {len(embedding)} "
                    f"(expected {settings.embedding_dimensions})"
                )

            return embedding

        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise OpenAIError(f"Failed to generate embedding: {e!s}") from e

    def _get_mime_type(self, file_path: Path) -> str:
        """
        Get MIME type from file extension.
        """
        ext_to_mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".heic": "image/heic",
            ".heif": "image/heif",
        }
        return ext_to_mime.get(file_path.suffix.lower(), "image/jpeg")

    async def batch_analyze(
        self, upload_ids: list[UUID], max_concurrent: int = 3
    ) -> None:
        """
        Analyze multiple uploads concurrently.

        Args:
            upload_ids: List of upload IDs to process
            max_concurrent: Max concurrent API calls
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(upload_id: UUID):
            async with semaphore:
                try:
                    await self.analyze_media(upload_id)
                except Exception as e:
                    logger.error(f"Batch processing failed for {upload_id}: {e}")

        # Process all uploads
        tasks = [process_with_limit(upload_id) for upload_id in upload_ids]
        await asyncio.gather(*tasks)

    async def test_connectivity(self) -> dict[str, bool]:
        """
        Test connectivity to AI services.

        Returns:
            Dict with service availability
        """
        results = {"gemini": False, "openai": False}

        # Test Gemini
        try:
            test_response = await self._call_gemini_async(
                prompt="Say 'Hello'",
                image_data=self._create_test_image(),
                mime_type="image/png",
            )
            results["gemini"] = bool(test_response)
        except Exception as e:
            logger.error(f"Gemini connectivity test failed: {e}")

        # Test OpenAI
        try:
            test_embedding = await self._generate_embedding("Test")
            results["openai"] = len(test_embedding) == settings.embedding_dimensions
        except Exception as e:
            logger.error(f"OpenAI connectivity test failed: {e}")

        return results

    def _create_test_image(self) -> bytes:
        """
        Create a small test image for connectivity testing.
        """
        # Create 100x100 white image
        img = Image.new("RGB", (100, 100), color="white")

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()


# Global instance
ai_service = AIService()
