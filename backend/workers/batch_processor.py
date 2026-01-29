"""
ⒸAngelaMos | 2026
batch_processor.py

- Sequential processing (one upload at a time, limited compute)
- Database is source of truth (worker crash = resume from DB state)
- Non-blocking failures (one bad upload doesn't stop the batch)
- Retry once per upload (fails twice = permanent failure, continue batch)
- WebSocket progress updates for real-time tracking
- Extreme timeouts (can run for days)
"""

import asyncio
import logging
import threading
from uuid import UUID

import dramatiq

import database
from core.tasks import broker
from core.redis import redis_pool
from core.websocket import (
    init_publisher,
)
from models.Upload import (
    Upload,
    ProcessingStatus,
)
from models.UploadBatch import (
    UploadBatch,
    BatchStatus,
)
from services.ai.service import LocalAIService

from .batch_helpers import (
    publish_batch_progress,
    publish_file_progress,
    process_upload_with_retry,
)


logger = logging.getLogger(__name__)

# Thread-local storage for event loop and initialization state
_thread_local = threading.local()


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get or create event loop for current thread

    Returns:
        Event loop instance
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop


async def ensure_worker_initialized() -> None:
    """
    Ensure worker thread is initialized (database, Redis, publisher)

    Idempotent - safe to call multiple times, only initializes once per thread
    """
    if getattr(_thread_local, 'initialized', False):
        return

    # Initialize database connection
    await database.db.connect()

    # Initialize Redis connection pool
    await redis_pool.connect()

    # Initialize WebSocket publisher (for publishing to Redis only - no listener needed)
    init_publisher()

    _thread_local.initialized = True
    logger.info("Worker thread initialized")


@dramatiq.actor(
    broker = broker,
    max_retries = 0,  # Retries manually at the upload level
    priority = 0,  # All batches equal priority (FIFO)
    time_limit = 7 * 24 * 60 * 60 * 1000,  # 7 days
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
    # String UUID back to UUID
    batch_uuid = UUID(batch_id)

    # Get or create event loop for this thread
    loop = get_or_create_event_loop()

    # Run async processing
    loop.run_until_complete(_process_batch_async(batch_uuid))


async def _process_batch_async(batch_id: UUID) -> None:
    """
    Async implementation of batch processing

    Args:
        batch_id: UUID of the batch to process
    """
    # Initialize worker thread (idempotent - only runs once per thread)
    await ensure_worker_initialized()

    logger.info(f"Starting batch processing for batch {batch_id}")

    batch = await UploadBatch.find_by_id(batch_id)
    if not batch:
        logger.error(f"Batch {batch_id} not found")
        return

    if batch.status in (BatchStatus.COMPLETED, BatchStatus.CANCELLED):
        logger.info(f"Batch {batch_id} already {batch.status}, skipping")
        return

    await batch.update_status(BatchStatus.PROCESSING)
    logger.info(
        f"Batch {batch_id} marked as processing: "
        f"{batch.total_uploads} uploads to process"
    )

    await publish_batch_progress(batch)

    query = """
        SELECT * FROM uploads
        WHERE batch_id = $1
        ORDER BY created_at ASC
    """
    records = await database.db.fetch(query, batch_id)
    uploads = Upload.from_records(records)

    if len(uploads) != batch.total_uploads:
        logger.warning(
            f"Batch {batch_id} expected {batch.total_uploads} uploads "
            f"but found {len(uploads)}"
        )

    ai_service = LocalAIService()

    for upload in uploads:
        if upload.processing_status == ProcessingStatus.COMPLETED:
            logger.info(
                f"Upload {upload.id} already completed, skipping "
                f"({batch.processed_uploads + 1}/{batch.total_uploads})"
            )
            await batch.increment_progress(successful = True)
            await publish_batch_progress(batch)
            continue

        logger.info(
            f"Processing upload {upload.id} "
            f"({batch.processed_uploads + 1}/{batch.total_uploads})"
        )

        # Publish file progress: starting
        await publish_file_progress(batch, upload, status="processing", progress=0)

        success = await process_upload_with_retry(ai_service, upload, batch)

        # Publish file progress: completed or failed
        final_status = "completed" if success else "failed"
        await publish_file_progress(batch, upload, status=final_status, progress=100)

        await batch.increment_progress(successful = success)
        await publish_batch_progress(batch)

        logger.info(
            f"Upload {upload.id} {'succeeded' if success else 'failed'} "
            f"(batch progress: {batch.processed_uploads}/{batch.total_uploads})"
        )

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

    await publish_batch_progress(batch)



