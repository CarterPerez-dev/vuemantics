"""
ⒸAngelaMos | 2026
batch_processor.py - Dramatiq worker for processing upload batches

ROBUSTNESS DESIGN:
- Sequential processing (one upload at a time, limited compute)
- Database is source of truth (worker crash = resume from DB state)
- Non-blocking failures (one bad upload doesn't stop the batch)
- Retry once per upload (fails twice = permanent failure, continue batch)
- WebSocket progress updates for real-time tracking
- Extreme timeouts (can run for days)
"""

import asyncio
import logging
from uuid import UUID

import dramatiq

from core.tasks import broker
from core.websocket import get_publisher, BatchProgressUpdate, BatchProgressPayload
from models.Upload import Upload, ProcessingStatus
from models.UploadBatch import UploadBatch, BatchStatus
from services.ai.service import LocalAIService


logger = logging.getLogger(__name__)


@dramatiq.actor(
    broker=broker,
    max_retries=0,  # We handle retries manually at the upload level
    priority=0,  # All batches equal priority (FIFO)
    time_limit=7 * 24 * 60 * 60 * 1000,  # 7 days
)
def process_batch(batch_id: str) -> None:
    """
    Process all uploads in a batch sequentially

    Args:
        batch_id: UUID of the batch to process

    Design:
    - Runs in background worker process
    - Processes uploads one by one (sequential)
    - Updates batch progress after each upload
    - Broadcasts WebSocket updates
    - If worker crashes, batch stays in 'processing' state
      and can be resumed by restarting the worker
    """
    # Convert string UUID back to UUID
    batch_uuid = UUID(batch_id)

    # Run async processing in event loop
    asyncio.run(_process_batch_async(batch_uuid))


async def _process_batch_async(batch_id: UUID) -> None:
    """
    Async implementation of batch processing

    Args:
        batch_id: UUID of the batch to process
    """
    logger.info(f"Starting batch processing for batch {batch_id}")

    # Load batch from database
    batch = await UploadBatch.find_by_id(batch_id)
    if not batch:
        logger.error(f"Batch {batch_id} not found")
        return

    # Check if already completed
    if batch.status in (BatchStatus.COMPLETED, BatchStatus.CANCELLED):
        logger.info(f"Batch {batch_id} already {batch.status}, skipping")
        return

    # Mark as processing
    await batch.update_status(BatchStatus.PROCESSING)
    logger.info(
        f"Batch {batch_id} marked as processing: "
        f"{batch.total_uploads} uploads to process"
    )

    # Broadcast batch started
    await _publish_batch_progress(batch)

    # Get all uploads for this batch
    query = """
        SELECT * FROM uploads
        WHERE batch_id = $1
        ORDER BY created_at ASC
    """

    import database
    records = await database.db.fetch(query, batch_id)
    uploads = Upload.from_records(records)

    if len(uploads) != batch.total_uploads:
        logger.warning(
            f"Batch {batch_id} expected {batch.total_uploads} uploads "
            f"but found {len(uploads)}"
        )

    # Initialize AI service
    ai_service = LocalAIService()

    # Process each upload sequentially
    for upload in uploads:
        # Skip if already completed successfully
        if upload.processing_status == ProcessingStatus.COMPLETED:
            logger.info(
                f"Upload {upload.id} already completed, skipping "
                f"({batch.processed_uploads + 1}/{batch.total_uploads})"
            )
            await batch.increment_progress(successful=True)
            await _publish_batch_progress(batch)
            continue

        logger.info(
            f"Processing upload {upload.id} "
            f"({batch.processed_uploads + 1}/{batch.total_uploads})"
        )

        # Process upload with retry logic
        success = await _process_upload_with_retry(ai_service, upload)

        # Update batch progress
        await batch.increment_progress(successful=success)
        await _publish_batch_progress(batch)

        logger.info(
            f"Upload {upload.id} {'succeeded' if success else 'failed'} "
            f"(batch progress: {batch.processed_uploads}/{batch.total_uploads})"
        )

    # Mark batch as complete
    if batch.failed_uploads == 0:
        await batch.update_status(BatchStatus.COMPLETED)
        logger.info(
            f"Batch {batch_id} completed successfully: "
            f"{batch.successful_uploads}/{batch.total_uploads} uploads processed"
        )
    else:
        await batch.update_status(BatchStatus.COMPLETED)
        logger.warning(
            f"Batch {batch_id} completed with failures: "
            f"{batch.successful_uploads} succeeded, "
            f"{batch.failed_uploads} failed out of {batch.total_uploads}"
        )

    # Final progress broadcast
    await _publish_batch_progress(batch)


async def _process_upload_with_retry(
    ai_service: LocalAIService,
    upload: Upload,
) -> bool:
    """
    Process a single upload with retry logic

    Args:
        ai_service: AI service instance
        upload: Upload to process

    Returns:
        True if successful, False if failed after retry

    Design:
    - Try once, retry once on failure (max 2 attempts)
    - Failures don't stop batch processing
    - Upload marked as failed after 2 attempts
    """
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                f"Processing upload {upload.id} (attempt {attempt}/{max_attempts})"
            )

            # Run AI analysis
            await ai_service.analyze_media(upload.id)

            # Refresh upload to get latest status
            await upload.refresh()

            if upload.processing_status == ProcessingStatus.COMPLETED:
                logger.info(f"Upload {upload.id} processed successfully")
                return True

            # Status not completed, treat as failure
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
                exc_info=True,
            )

            if attempt < max_attempts:
                logger.info(
                    f"Retrying upload {upload.id} after error (attempt {attempt + 1}/{max_attempts})"
                )
                continue

    # Failed after all retries
    logger.error(
        f"Upload {upload.id} failed after {max_attempts} attempts, marking as failed"
    )

    try:
        await upload.update_status(
            ProcessingStatus.FAILED,
            error_message="Failed after retry",
        )
    except Exception as update_err:
        logger.error(
            f"Failed to update status for {upload.id}: {update_err}"
        )

    return False


async def _publish_batch_progress(batch: UploadBatch) -> None:
    """
    Publish batch progress update via WebSocket

    Args:
        batch: UploadBatch instance
    """
    try:
        publisher = get_publisher()
        await publisher.publish_to_user(
            batch.user_id,
            BatchProgressUpdate(
                payload=BatchProgressPayload(
                    batch_id=batch.id,
                    status=batch.status,
                    total=batch.total_uploads,
                    processed=batch.processed_uploads,
                    successful=batch.successful_uploads,
                    failed=batch.failed_uploads,
                    progress_percentage=batch.get_progress_percentage(),
                )
            ),
        )
    except Exception as e:
        # Don't fail batch processing if WebSocket broadcast fails
        logger.warning(f"Failed to publish batch progress for {batch.id}: {e}")
