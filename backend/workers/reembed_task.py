"""
©AngelaMos | 2026
reembed_task.py
"""

import asyncio
import logging
from uuid import UUID

import dramatiq

import config
import database
from core.tasks import broker
from core.websocket import (
    ReembedComplete,
    ReembedProgress,
    get_publisher,
)
from models.Upload import ProcessingStatus, Upload
from services.ai.providers.factory import get_provider
from workers.batch_processor import ensure_worker_initialized, get_or_create_event_loop


logger = logging.getLogger(__name__)

REEMBED_BATCH_SIZE = 50


@dramatiq.actor(
    broker=broker,
    max_retries=0,
    time_limit=7 * 24 * 60 * 60 * 1000,
)
def reembed_all(user_id_str: str) -> None:
    loop = get_or_create_event_loop()
    loop.run_until_complete(_reembed_all_async(UUID(user_id_str)))


async def _reembed_all_async(user_id: UUID) -> None:
    await ensure_worker_initialized()

    provider = await get_provider()
    publisher = get_publisher()

    total = await database.db.fetchval(
        "SELECT COUNT(*) FROM uploads WHERE processing_status = $1 AND hidden = FALSE",
        ProcessingStatus.COMPLETED,
    ) or 0
    total = int(total)

    processed = skipped = failed = 0
    offset = 0

    logger.info(
        f"Starting re-embed of {total} uploads with provider={provider.provider_name}"
    )

    while True:
        records = await database.db.fetch(
            """
            SELECT * FROM uploads
            WHERE processing_status = $1 AND hidden = FALSE
            ORDER BY created_at ASC
            LIMIT $2 OFFSET $3
            """,
            ProcessingStatus.COMPLETED,
            REEMBED_BATCH_SIZE,
            offset,
        )
        uploads = Upload.from_records(records)

        if not uploads:
            break

        for upload in uploads:
            file_path = config.settings.upload_path / upload.file_path

            if not file_path.exists():
                logger.warning(f"File missing for upload {upload.id}, skipping")
                skipped += 1
                continue

            if provider.provider_name == "gemini":
                from services.ai.providers.gemini import (
                    GEMINI_SUPPORTED_IMAGE_MIMES,
                    GEMINI_SUPPORTED_VIDEO_MIMES,
                )
                if upload.file_type == "video" and upload.mime_type not in GEMINI_SUPPORTED_VIDEO_MIMES:
                    logger.warning(
                        f"Unsupported video format for Gemini: {upload.mime_type} ({upload.id}), skipping"
                    )
                    skipped += 1
                    continue

            try:
                await upload.update_status(ProcessingStatus.PENDING)
                await provider.process_upload(upload)
                await upload.refresh()

                if upload.processing_status == ProcessingStatus.COMPLETED:
                    processed += 1
                else:
                    failed += 1
                    await upload.update_status(
                        ProcessingStatus.COMPLETED,
                        error_message=None,
                    )

            except Exception as e:
                logger.error(f"Re-embed failed for {upload.id}: {e}")
                failed += 1
                try:
                    await upload.update_status(ProcessingStatus.COMPLETED)
                except Exception:
                    pass

            progress_msg = ReembedProgress(
                processed=processed,
                total=total,
                skipped=skipped,
                failed=failed,
            )
            await publisher.publish_to_user(str(user_id), progress_msg)

        offset += REEMBED_BATCH_SIZE

    complete_msg = ReembedComplete(
        processed=processed,
        skipped=skipped,
        failed=failed,
    )
    await publisher.publish_to_user(str(user_id), complete_msg)
    logger.info(
        f"Re-embed complete: processed={processed}, skipped={skipped}, failed={failed}"
    )
