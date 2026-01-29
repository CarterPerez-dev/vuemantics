"""
ⒸAngelaMos | 2026
_process_upload_with_retry.py

Process single upload with retry logic and progress monitoring
"""

import asyncio
import contextlib
import logging

from models.Upload import Upload, ProcessingStatus
from models.UploadBatch import UploadBatch
from services.ai import LocalAIService
from services.storage_service import storage_service

from ._publish_file_progress import publish_file_progress


logger = logging.getLogger(__name__)


async def process_upload_with_retry(
    ai_service: LocalAIService,
    upload: Upload,
    batch: UploadBatch,
) -> bool:
    """
    Process a single upload with retry logic

    Args:
        ai_service: AI service instance
        upload: Upload to process
        batch: UploadBatch instance for progress updates

    Returns:
        True if successful, False if failed after retry

    Design:
    - Try once, retry once on failure (max 2 attempts)
    - Failures don't stop batch processing
    - Upload marked as failed after 2 attempts
    - Publishes real-time progress by monitoring AI service stages
    """
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                f"Processing upload {upload.id} (attempt {attempt}/{max_attempts})"
            )

            # Generate thumbnail (only on first attempt)
            if attempt == 1 and not upload.thumbnail_path:
                try:
                    logger.info(f"Generating thumbnail for upload {upload.id}")
                    await publish_file_progress(batch, upload, status="processing", progress=5)
                    thumbnail_path = await storage_service.generate_thumbnail(
                        user_id = upload.user_id,
                        upload_id = upload.id,
                        file_type = upload.file_type,
                        extension = upload.file_path.split('.')[-1],
                    )
                    if thumbnail_path:
                        await upload.update_thumbnail(thumbnail_path)
                        logger.info(f"Thumbnail generated for upload {upload.id}")
                    await publish_file_progress(batch, upload, status="processing", progress=10)
                except Exception as thumb_error:
                    logger.warning(
                        f"Thumbnail generation failed for {upload.id}: {thumb_error}"
                    )
                    # Continue processing even if thumbnail fails

            # Monitor AI progress with real stages
            async def monitor_ai_progress() -> None:
                """Poll upload status and publish real progress from AI service"""
                last_progress = 10
                start_time = asyncio.get_event_loop().time()

                while True:
                    await asyncio.sleep(0.3)  # Poll every 300ms

                    try:
                        await upload.refresh()
                    except ValueError:
                        # Upload was deleted mid-processing (user action)
                        logger.warning(f"Upload {upload.id} was deleted during processing, stopping monitor")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to refresh upload {upload.id}: {e}")
                        await asyncio.sleep(1.0)  # Back off and retry
                        continue

                    elapsed = asyncio.get_event_loop().time() - start_time

                    # Map AI service's internal stages to progress %
                    # (AI service publishes to single upload channel, we republish for batch)
                    if upload.processing_status == "analyzing":
                        # Vision analysis: 10-75% (the long phase)
                        # Gradually increase based on time (slower after 50%)
                        if last_progress < 50:
                            progress = min(50, last_progress + 2)
                        else:
                            # Slower increment after 50%: ~1% per second
                            time_progress = 50 + min(25, int(elapsed / 1.0))
                            progress = max(last_progress, time_progress)
                    elif upload.processing_status == "embedding":
                        # Embedding generation: 75-90%
                        progress = min(90, max(75, last_progress + 2))
                    else:
                        break

                    if progress > last_progress:
                        await publish_file_progress(batch, upload, status="processing", progress=progress)
                        last_progress = progress

            # Start progress monitor and AI analysis concurrently
            monitor_task = asyncio.create_task(monitor_ai_progress())
            try:
                await ai_service.analyze_media(upload.id)
            finally:
                monitor_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await monitor_task

            await upload.refresh()

            if upload.processing_status == ProcessingStatus.COMPLETED:
                logger.info(f"Upload {upload.id} processed successfully")
                return True

            logger.warning(
                f"Upload {upload.id} processing incomplete "
                f"(status={upload.processing_status})"
            )

            if attempt < max_attempts:
                logger.info(
                    f"Retrying upload {upload.id} (attempt {attempt + 1}/{max_attempts})"
                )
                continue

        except Exception as e:
            logger.error(
                f"Error processing upload {upload.id} (attempt {attempt}/{max_attempts}): {e}",
                exc_info = True,
            )

            if attempt < max_attempts:
                logger.info(
                    f"Retrying upload {upload.id} after error (attempt {attempt + 1}/{max_attempts})"
                )
                continue

    logger.error(
        f"Upload {upload.id} failed after {max_attempts} attempts, marking as failed"
    )

    try:
        await upload.update_status(
            ProcessingStatus.FAILED,
            error_message = "Failed after retry",
        )
    except Exception as update_err:
        logger.error(
            f"Failed to update status for {upload.id}: {update_err}"
        )

    return False
