"""
ⒸAngelaMos | 2026
_publish_file_progress.py

Publish per-file progress updates via WebSocket
"""

import logging

from core.websocket import (
    get_publisher,
    FileProgressUpdate,
    FileProgressPayload,
)
from models.Upload import Upload
from models.UploadBatch import UploadBatch


logger = logging.getLogger(__name__)


async def publish_file_progress(
    batch: UploadBatch,
    upload: Upload,
    status: str,
    progress: int = 0,
) -> None:
    """
    Publish per-file progress update via WebSocket

    Args:
        batch: UploadBatch instance
        upload: Upload instance
        status: File processing status (processing/completed/failed)
        progress: Progress percentage (0-100)
    """
    try:
        publisher = get_publisher()

        await publisher.publish_to_user(
            str(batch.user_id),
            FileProgressUpdate(
                payload = FileProgressPayload(
                    batch_id = str(batch.id),
                    upload_id = str(upload.id),
                    file_name = upload.filename,
                    file_size = upload.file_size or 0,
                    progress_percentage = progress,
                    status = status,
                )
            ),
        )
    except Exception as e:
        # Don't fail batch processing if WebSocket broadcast fails
        logger.warning(
            f"Failed to publish file progress for {upload.id}: {e}"
        )
