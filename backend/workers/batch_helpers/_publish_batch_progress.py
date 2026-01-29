"""
ⒸAngelaMos | 2026
_publish_batch_progress.py

Publish batch-level progress updates via WebSocket
"""

import logging

from core.websocket import (
    get_publisher,
    BatchProgressUpdate,
    BatchProgressPayload,
)
from models.UploadBatch import UploadBatch


logger = logging.getLogger(__name__)


async def publish_batch_progress(batch: UploadBatch) -> None:
    """
    Publish batch progress update via WebSocket

    Args:
        batch: UploadBatch instance
    """
    try:
        publisher = get_publisher()
        await publisher.publish_to_user(
            str(batch.user_id),
            BatchProgressUpdate(
                payload = BatchProgressPayload(
                    batch_id = str(batch.id),
                    status = batch.status,
                    total = batch.total_uploads,
                    processed = batch.processed_uploads,
                    successful = batch.successful_uploads,
                    failed = batch.failed_uploads,
                    progress_percentage = int(batch.get_progress_percentage()),
                )
            ),
        )
    except Exception as e:
        # Don't fail batch processing if WebSocket broadcast fails
        logger.warning(
            f"Failed to publish batch progress for {batch.id}: {e}"
        )
