"""
ⒸAngelaMos | 2026
regenerate.py

"""

import asyncio
import logging

from models.Upload import ProcessingStatus, Upload
from core import ConflictError, ValidationError
from services.ai.service import local_ai_service


logger = logging.getLogger(__name__)


async def regenerate_upload_description(upload: Upload) -> None:
    """
    Regenerate AI generated description for an upload

    Args:
        upload: Upload instance to regenerate
    """
    # Validate status - prevent duplicate work
    if upload.processing_status == ProcessingStatus.ANALYZING:
        raise ConflictError(
            "Upload is already being analyzed. Please wait for completion."
        )

    if upload.processing_status not in (ProcessingStatus.COMPLETED,
                                        ProcessingStatus.FAILED):
        raise ValidationError(
            f"Cannot regenerate description for upload with status: "
            f"{upload.processing_status}. Only 'completed' or 'failed' "
            f"uploads can be regenerated."
        )

    # Update regeneration metadata (atomic increment)
    await upload.update_regeneration_metadata()
    logger.info(
        f"Regeneration #{upload.regeneration_count} initiated for upload {upload.id}"
    )

    # Set status to analyzing (keeps old description visible)
    await upload.update_status(ProcessingStatus.ANALYZING)

    # Queue background AI processing (reuse existing pipeline)
    task = asyncio.create_task(local_ai_service.analyze_media(upload.id))
    task.add_done_callback(lambda t: t.exception())

    logger.debug(
        f"Queued AI analysis for upload {upload.id} "
        f"(regeneration #{upload.regeneration_count})"
    )
