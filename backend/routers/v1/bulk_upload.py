"""
ⒸAngelaMos | 2026
bulk_upload.py
"""

import logging
from uuid import UUID
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Request,
    UploadFile,
    status,
)

import config
from auth import get_current_user
from core import (
    AUTH_401,
    CONFLICT_409,
    FILE_TOO_LARGE_413,
    NOT_FOUND_404,
    RATE_LIMIT_420,
    SERVER_ERROR_500,
    UNSUPPORTED_MEDIA_415,
    VALIDATION_422,
    limiter,
)
from models.User import User
from services.bulk_upload_service import (
    bulk_upload_service,
    BulkUploadResult,
    BatchStatusResult,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/uploads",
    tags = ["bulk-uploads"],
    responses = {
        **AUTH_401,
        **NOT_FOUND_404,
        **CONFLICT_409,
        **FILE_TOO_LARGE_413,
        **UNSUPPORTED_MEDIA_415,
        **VALIDATION_422,
        **RATE_LIMIT_420,
        **SERVER_ERROR_500,
    },
)


@router.post(
    "/bulk",
    response_model = BulkUploadResult,
    status_code = status.HTTP_201_CREATED,
    summary = "Bulk upload files",
    description = "Upload multiple files for background processing",
)
@limiter.limit(config.settings.rate_limit_bulk_upload)
async def bulk_upload(
    request: Request,
    files: Annotated[list[UploadFile],
                     File(description = "Files to upload")],
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> BulkUploadResult:
    """
    Upload multiple files as a batch
    """
    result = await bulk_upload_service.create_bulk_upload(
        user_id = current_user.id,
        files = files,
    )

    logger.info(
        f"User {current_user.id} created bulk upload batch {result.batch_id}: "
        f"{result.queued} queued, {result.failed} failed"
    )

    return result


@router.get(
    "/batches/{batch_id}",
    response_model = BatchStatusResult,
    summary = "Get batch status",
    description = "Get processing status for a batch",
)
@limiter.limit(config.settings.rate_limit_batch_status)
async def get_batch_status(
    request: Request,
    batch_id: UUID,
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> BatchStatusResult:
    """
    Get batch status with progress information
    """
    return await bulk_upload_service.get_batch_status(
        batch_id = batch_id,
        user_id = current_user.id,
    )


@router.post(
    "/batches/{batch_id}/cancel",
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Cancel batch",
    description = "Cancel a running batch upload",
)
@limiter.limit(config.settings.rate_limit_batch_status)
async def cancel_batch(
    request: Request,
    batch_id: UUID,
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> None:
    """
    Cancel a batch that's currently processing
    """
    await bulk_upload_service.cancel_batch(
        batch_id = batch_id,
        user_id = current_user.id,
    )

    logger.info(f"User {current_user.id} cancelled batch {batch_id}")


@router.get(
    "/batches",
    response_model = list[BatchStatusResult],
    summary = "List user batches",
    description = "Get list of user's upload batches",
)
@limiter.limit(config.settings.rate_limit_batch_list)
async def list_batches(
    request: Request,
    current_user: Annotated[User,
                            Depends(get_current_user)],
    limit: int = config.BATCH_LIST_DEFAULT_LIMIT,
    offset: int = config.BATCH_LIST_DEFAULT_OFFSET,
) -> list[BatchStatusResult]:
    """
    List user's batches with pagination
    """
    return await bulk_upload_service.list_user_batches(
        user_id = current_user.id,
        limit = limit,
        offset = offset,
    )
