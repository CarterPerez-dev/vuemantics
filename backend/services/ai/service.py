"""
ⒸAngelaMos | 2026
service.py
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

import config
from core import VisionError
from core.validators import DescriptionAuditor
from core.websocket import (
    get_publisher,
    ProcessingStage,
    UploadProgressUpdate,
    UploadProgressPayload,
    UploadCompleted,
    UploadFailed,
)
from models.Upload import Upload, ProcessingStatus
from services.storage_service import storage_service
from services.ai.embedding import EmbeddingService
from services.ai.manager import OllamaManager
from services.ai.vision import VisionService


logger = logging.getLogger(__name__)


class LocalAIService:
    """
    Handles AI processing using local Ollama models

    Workflow:
    1. Analyze media with Qwen2.5-VL to get text description
    2. Generate embedding from description using bge-m3
    3. Update upload record with results
    """
    def __init__(self) -> None:
        """
        Initialize local AI service.
        """
        self._ollama = OllamaManager()
        self._vision_semaphore = asyncio.Semaphore(
            config.VISION_SEMAPHORE_LIMIT
        )
        self._embedding_semaphore = asyncio.Semaphore(
            config.EMBEDDING_SEMAPHORE_LIMIT
        )

        self._vision = VisionService(self._ollama, self._vision_semaphore)
        self._embedding = EmbeddingService(
            self._ollama,
            self._embedding_semaphore
        )

        logger.info("Local AI service initialized (Ollama-based)")

    async def _publish_progress(
        self,
        upload_id: UUID,
        status: ProcessingStatus,
        stage: ProcessingStage,
        progress_percent: int,
        message: str,
        error_message: str | None = None,
        audit_score: int | None = None,
    ) -> None:
        """
        Publish upload progress via WebSocket

        Args:
            upload_id: Upload's ID
            status: Current processing status
            stage: Current processing stage
            progress_percent: Progress percentage (0-100)
            message: Human-readable message
            error_message: Error details if failed
            audit_score: Description quality score if available
        """
        try:
            publisher = get_publisher()
            progress_msg = UploadProgressUpdate(
                payload=UploadProgressPayload(
                    upload_id=str(upload_id),
                    status=status,
                    stage=stage,
                    progress_percent=progress_percent,
                    message=message,
                    error_message=error_message,
                    description_audit_score=audit_score,
                ),
                timestamp=datetime.utcnow(),
            )
            await publisher.publish_progress(str(upload_id), progress_msg)
        except Exception as e:
            logger.warning(f"Failed to publish progress for {upload_id}: {e}")

    async def analyze_media(self, upload_id: UUID) -> None:
        """
        Analyze media file and generate embeddings.

        Args:
            upload_id: Upload to process

        Updates upload record with:
        - description: Text description
        - embedding_local: 1024-dimensional vector
        - processing_status: completed or failed
        """
        upload = await Upload.find_by_id(upload_id)
        if not upload:
            logger.error(f"Upload {upload_id} not found")
            return

        try:
            await upload.update_status(ProcessingStatus.ANALYZING)
            await self._publish_progress(
                upload_id,
                ProcessingStatus.ANALYZING,
                ProcessingStage.QUEUED,
                0,
                "Starting AI analysis"
            )
            logger.info(
                f"Starting local AI analysis for upload {upload_id}"
            )

            file_path = config.settings.upload_path / upload.file_path

            description = None
            audit_result = None
            max_retries = 2

            for attempt in range(max_retries):
                if upload.file_type == "video":
                    await self._publish_progress(
                        upload_id,
                        ProcessingStatus.ANALYZING,
                        ProcessingStage.EXTRACTING_FRAMES,
                        10,
                        "Extracting video frames"
                    )

                await self._publish_progress(
                    upload_id,
                    ProcessingStatus.ANALYZING,
                    ProcessingStage.VISION_ANALYSIS,
                    20,
                    f"Analyzing {upload.file_type} with vision model"
                )

                if upload.file_type == "image":
                    description = await self._vision.analyze_image(
                        file_path
                    )
                else:
                    description = await self._analyze_video_with_frames(
                        upload.user_id,
                        upload_id,
                        file_path
                    )

                if not description:
                    raise VisionError(
                        "Vision model returned empty description"
                    )

                await self._publish_progress(
                    upload_id,
                    ProcessingStatus.ANALYZING,
                    ProcessingStage.DESCRIPTION_AUDIT,
                    50,
                    "Auditing description quality"
                )

                audit_result = DescriptionAuditor.audit(description)
                logger.info(
                    f"Description audit for {upload_id}: score={audit_result.score}, "
                    f"passed={audit_result.passed}, issues={audit_result.issues}"
                )

                if audit_result.passed:
                    break

                if attempt < max_retries - 1:
                    logger.warning(
                        f"Description failed audit (attempt {attempt + 1}/{max_retries}), "
                        f"retrying... Issues: {audit_result.issues}"
                    )

            if audit_result is None or description is None:
                raise VisionError("Failed to generate valid description")

            if not audit_result.passed:
                logger.warning(
                    f"Description for {upload_id} has low quality score: {audit_result.score}"
                )

            logger.info(
                f"Vision analysis complete for {upload_id}: {len(description)} chars, "
                f"audit_score={audit_result.score}"
            )

            await upload.update_status(ProcessingStatus.EMBEDDING)
            await self._publish_progress(
                upload_id,
                ProcessingStatus.EMBEDDING,
                ProcessingStage.EMBEDDING_GENERATION,
                60,
                "Generating embeddings",
                audit_score=audit_result.score
            )

            logger.info(f"Starting embedding generation for {upload_id}")
            embedding = await self._embedding.generate_embedding(
                description
            )
            logger.info(
                f"Generated embedding for {upload_id}: {len(embedding)} dimensions"
            )

            await self._publish_progress(
                upload_id,
                ProcessingStatus.EMBEDDING,
                ProcessingStage.INDEXING,
                90,
                "Updating database",
                audit_score=audit_result.score
            )

            logger.info(
                f"Updating database with analysis results for {upload_id}"
            )
            await upload.update_analysis(
                description = description,
                embedding = embedding,
                use_local = True,
                description_audit_score = audit_result.score,
            )

            # Publish completion
            completed_msg = UploadCompleted(
                upload_id=str(upload_id),
                description=description,
                audit_score=audit_result.score,
                timestamp=datetime.utcnow(),
            )
            await get_publisher().publish_progress(str(upload_id), completed_msg)

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

            # Publish failure
            failed_msg = UploadFailed(
                upload_id=str(upload_id),
                error_message=str(e)[:500],
                timestamp=datetime.utcnow(),
            )
            await get_publisher().publish_progress(str(upload_id), failed_msg)

    async def _analyze_video_with_frames(
        self,
        user_id: UUID,
        upload_id: UUID,
        video_path: Path
    ) -> str:
        """
        Extract frames and analyze video.

        Args:
            user_id: User ID
            upload_id: Upload ID
            video_path: Path to video file

        Returns:
            Text description of video content
        """
        extension = video_path.suffix[1 :]
        frame_paths = await storage_service.extract_video_frames(
            user_id = user_id,
            upload_id = upload_id,
            extension = extension,
            max_frames = config.settings.max_video_frames,
        )

        if not frame_paths:
            raise VisionError("No frames extracted from video")

        full_frame_paths = [
            config.settings.upload_path / frame_path for frame_path in
            frame_paths[: config.MAX_VIDEO_FRAMES_FOR_ANALYSIS]
        ]

        return await self._vision.analyze_video(full_frame_paths)

    async def create_embedding_for_query(self, query: str) -> list[float]:
        """
        Generate embedding for search query.

        Args:
            query: Search query text

        Returns:
            1024-dimensional embedding vector
        """
        return await self._embedding.create_query_embedding(query)

    async def batch_analyze(
        self,
        upload_ids: list[UUID],
        max_concurrent: int = config.BATCH_ANALYZE_MAX_CONCURRENT
    ) -> None:
        """
        Analyze multiple uploads concurrently.

        Args:
            upload_ids: List of upload IDs to process
            max_concurrent: Max concurrent processing
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(upload_id: UUID) -> None:
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
            model_names = await self._ollama.list_models()

            vision_name = config.settings.vision_model.split(":")[0]
            embedding_name = config.settings.local_embedding_model.split(
                ":"
            )[0]

            results["vision"] = any(vision_name in n for n in model_names)
            results["embedding"] = any(
                embedding_name in n for n in model_names
            )

        except Exception as e:
            logger.error(f"Ollama connectivity test failed: {e}")

        return results


local_ai_service = LocalAIService()
