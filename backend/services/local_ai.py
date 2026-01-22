"""
Local AI service for media analysis and embedding generation.
Uses Ollama for BOTH Qwen2.5-VL (vision) and bge-m3 (embeddings).
Replaces cloud-based Gemini + OpenAI with local GPU models.
---
/backend/services/local_ai.py
"""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

import httpx
from ollama import AsyncClient, ResponseError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings
from models import ProcessingStatus, Upload
from services import storage_service


logger = logging.getLogger(__name__)


class LocalAIError(Exception):
    """
    Base exception for local AI service errors.
    """


class VisionError(LocalAIError):
    """
    Raised when Qwen2.5-VL inference fails.
    """


class EmbeddingError(LocalAIError):
    """
    Raised when bge-m3 embedding fails.
    """


class OllamaManager:
    """
    Manages Ollama client connection.
    """
    def __init__(self):
        """
        Initialize Ollama manager.
        """
        self._ollama_client: Optional[AsyncClient] = None

    async def get_client(self) -> AsyncClient:
        """
        Get or create Ollama async client.
        """
        if self._ollama_client is None:
            self._ollama_client = AsyncClient(
                host = settings.ollama_host,
                timeout = httpx.Timeout(
                    connect = 10.0,
                    read = 300.0,
                    write = 60.0,
                    pool = 30.0
                ),
            )
        return self._ollama_client


class LocalAIService:
    """
    Handles AI processing using local Ollama models.

    Workflow:
    1. Analyze media with Qwen2.5-VL to get text description
    2. Generate embedding from description using bge-m3
    3. Update upload record with results
    """
    def __init__(self):
        """
        Initialize local AI service.
        """
        self._ollama = OllamaManager()
        self._vision_semaphore = asyncio.Semaphore(1)
        self._embedding_semaphore = asyncio.Semaphore(3)

        logger.info("Local AI service initialized (Ollama-based)")

    async def analyze_media(self, upload_id: UUID) -> None:
        """
        Analyze media file and generate embeddings.

        Args:
            upload_id: Upload to process

        Updates upload record with:
        - gemini_summary: Text description
        - embedding_local: 1024-dimensional vector
        - processing_status: completed or failed
        """
        upload = await Upload.find_by_id(upload_id)
        if not upload:
            logger.error(f"Upload {upload_id} not found")
            return

        try:
            await upload.update_status(ProcessingStatus.ANALYZING)
            logger.info(
                f"Starting local AI analysis for upload {upload_id}"
            )

            file_path = settings.upload_path / upload.file_path

            if upload.file_type == "image":
                description = await self._analyze_image(file_path)
            else:
                description = await self._analyze_video(
                    upload.user_id,
                    upload_id,
                    file_path
                )

            if not description:
                raise VisionError(
                    "Vision model returned empty description"
                )

            logger.info(
                f"Vision analysis complete for {upload_id}: {len(description)} chars"
            )

            await upload.update_status(ProcessingStatus.EMBEDDING)

            logger.info(f"Starting embedding generation for {upload_id}")
            embedding = await self._generate_embedding(description)
            logger.info(
                f"Generated embedding for {upload_id}: {len(embedding)} dimensions"
            )

            logger.info(
                f"Updating database with analysis results for {upload_id}"
            )
            await upload.update_analysis(
                gemini_summary = description,
                embedding = embedding,
                use_local = True
            )

            logger.info(
                f"Local AI processing completed for upload {upload_id}"
            )

        except Exception as e:
            logger.error(
                f"Local AI processing failed for upload {upload_id}: {e}"
            )
            await upload.update_status(
                ProcessingStatus.FAILED,
                error_message = f"AI processing failed: {str(e)[:500]}",
            )

    @retry(
        retry = retry_if_exception_type(
            (httpx.TimeoutException,
             httpx.ConnectError)
        ),
        stop = stop_after_attempt(3),
        wait = wait_exponential(multiplier = 1,
                                min = 2,
                                max = 30),
    )
    async def _analyze_image(self, image_path: Path) -> str:
        """
        Analyze image with Qwen2.5-VL via Ollama.

        Args:
            image_path: Path to image file

        Returns:
            Text description of image content
        """
        try:
            async with self._vision_semaphore:
                with open(image_path, "rb") as f:
                    image_data = f.read()

                image_b64 = base64.b64encode(image_data).decode("utf-8")

                prompt = """Analyze this image and provide a detailed description that would help someone find it through text search.

Include:
- Main subjects (people, animals, objects)
- Actions or activities
- Setting/location
- Mood or atmosphere
- Notable colors or visual elements
- Any text visible in the image

Be specific and descriptive, using natural language that someone might use to search for this image."""

                client = await self._ollama.get_client()
                response = await client.chat(
                    model = settings.vision_model,
                    messages = [
                        {
                            "role": "user",
                            "content": prompt,
                            "images": [image_b64],
                        }
                    ],
                    options = {
                        "temperature": 0.3,
                        "num_predict": 512,
                    },
                )

                return response["message"]["content"].strip()

        except ResponseError as e:
            if e.status_code == 404:
                raise VisionError(
                    f"Model not loaded. Run: ollama pull {settings.vision_model}"
                ) from e
            raise VisionError(f"Vision model error: {e.error}") from e
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise VisionError(f"Failed to analyze image: {e!s}") from e

    async def _analyze_video(
        self,
        user_id: UUID,
        upload_id: UUID,
        video_path: Path
    ) -> str:
        """
        Analyze video with Qwen2.5-VL using extracted frames via Ollama.

        Args:
            user_id: User ID
            upload_id: Upload ID
            video_path: Path to video file

        Returns:
            Text description of video content
        """
        try:
            async with self._vision_semaphore:
                extension = video_path.suffix[1 :]
                frame_paths = await storage_service.extract_video_frames(
                    user_id = user_id,
                    upload_id = upload_id,
                    extension = extension,
                    max_frames = settings.max_video_frames,
                )

                if not frame_paths:
                    raise VisionError("No frames extracted from video")

                frames_b64 = []
                for frame_path in frame_paths[: 5]:
                    full_path = settings.upload_path / frame_path
                    with open(full_path, "rb") as f:
                        frame_data = f.read()
                        frames_b64.append(
                            base64.b64encode(frame_data).decode("utf-8")
                        )

                prompt = f"""Analyze these {len(frames_b64)} frames from a video and provide a comprehensive description.

Include:
- Main subjects and their actions throughout the video
- Changes or progression between frames
- Setting/location
- Overall theme or story
- Any text or important visual elements
- Mood or atmosphere

Describe it as a cohesive video, not individual frames. Be specific and use natural language that someone might use to search for this video."""

                client = await self._ollama.get_client()
                response = await client.chat(
                    model = settings.vision_model,
                    messages = [
                        {
                            "role": "user",
                            "content": prompt,
                            "images": frames_b64,
                        }
                    ],
                    options = {
                        "temperature": 0.3,
                        "num_predict": 1024,
                    },
                )

                return response["message"]["content"].strip()

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise VisionError(f"Failed to analyze video: {e!s}") from e

    @retry(
        retry = retry_if_exception_type(
            (httpx.TimeoutException,
             httpx.ConnectError)
        ),
        stop = stop_after_attempt(3),
        wait = wait_exponential(multiplier = 1,
                                min = 2,
                                max = 30),
    )
    async def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector from text using bge-m3 via Ollama.

        Args:
            text: Text to embed (vision description)

        Returns:
            1024-dimensional embedding vector
        """
        try:
            max_chars = 32000
            if len(text) > max_chars:
                text = text[: max_chars] + "..."
                logger.warning(
                    f"Truncated text from {len(text)} to {max_chars} chars"
                )

            async with self._embedding_semaphore:
                client = await self._ollama.get_client()
                response = await client.embeddings(
                    model = settings.local_embedding_model,
                    prompt = text,
                )

                embedding = response["embedding"]

                # DEBUG: Log what Ollama actually returned
                logger.info(f"[OLLAMA DEBUG] Embedding type: {type(embedding).__name__}")
                logger.info(f"[OLLAMA DEBUG] Embedding length: {len(embedding)}")
                if isinstance(embedding, list) and len(embedding) > 0:
                    logger.info(f"[OLLAMA DEBUG] First element type: {type(embedding[0]).__name__}")
                    logger.info(f"[OLLAMA DEBUG] First element value: {embedding[0]}")
                    if isinstance(embedding[0], list):
                        logger.error(f"[OLLAMA DEBUG] NESTED LIST DETECTED! Outer length: {len(embedding)}, Inner length: {len(embedding[0])}")

                if len(embedding) != 1024:
                    raise EmbeddingError(
                        f"Invalid embedding dimensions: {len(embedding)} "
                        "(expected 1024)"
                    )

                return embedding

        except ResponseError as e:
            if e.status_code == 404:
                raise EmbeddingError(
                    f"Model not loaded. Run: ollama pull {settings.local_embedding_model}"
                ) from e
            raise EmbeddingError(
                f"Embedding model error: {e.error}"
            ) from e
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(
                f"Failed to generate embedding: {e!s}"
            ) from e

    async def create_embedding_for_query(self, query: str) -> list[float]:
        """
        Generate embedding for search query.

        Args:
            query: Search query text

        Returns:
            1024-dimensional embedding vector
        """
        return await self._generate_embedding(query)

    async def batch_analyze(
        self,
        upload_ids: list[UUID],
        max_concurrent: int = 3
    ) -> None:
        """
        Analyze multiple uploads concurrently.

        Args:
            upload_ids: List of upload IDs to process
            max_concurrent: Max concurrent processing
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(upload_id: UUID):
            async with semaphore:
                try:
                    await self.analyze_media(upload_id)
                except Exception as e:
                    logger.error(
                        f"Batch processing failed for {upload_id}: {e}"
                    )

        tasks = [process_with_limit(upload_id) for upload_id in upload_ids]
        await asyncio.gather(*tasks)

    async def test_connectivity(self) -> dict[str, bool]:
        """
        Test connectivity to Ollama services.

        Returns:
            Dict with service availability
        """
        results = {"vision": False, "embedding": False}

        try:
            client = await self._ollama.get_client()
            models = await client.list()
            model_names = [m["name"] for m in models.get("models", [])]

            vision_name = settings.vision_model.split(":")[0]
            embedding_name = settings.local_embedding_model.split(":")[
                0
            ] if ":" in settings.local_embedding_model else settings.local_embedding_model

            results["vision"] = any(vision_name in n for n in model_names)
            results["embedding"] = any(
                embedding_name in n for n in model_names
            )

        except Exception as e:
            logger.error(f"Ollama connectivity test failed: {e}")

        return results


local_ai_service = LocalAIService()
