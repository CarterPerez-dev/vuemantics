"""
ⒸAngelaMos | 2026
upload.py
"""

import logging
import asyncio
import contextlib
from uuid import UUID, uuid4
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Request,
    UploadFile,
    status,
)

import config
from auth import (
    get_current_user, 
    verify_upload_ownership,
)
from core import (
    AUTH_401,
    CONFLICT_409,
    FILE_TOO_LARGE_413,
    NOT_FOUND_404,
    RATE_LIMIT_420,
    SERVER_ERROR_500,
    UNSUPPORTED_MEDIA_415,
    VALIDATION_422,
    ConflictError,
    NotFoundError,
    StorageError,
    ValidationError,
    limiter,
)
from models.User import User
from models.Upload import Upload, ProcessingStatus
from schemas import (
    PaginatedResponse,
    UploadListParams,
    UploadResponse,
)
from services.ai import (
    local_ai_service,
    regenerate_upload_description,
)    
from services.storage_service import storage_service


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/uploads",
    tags = ["uploads"],
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


async def process_upload_background(
    upload_id: UUID,
    user_id: UUID,
    file_type: str,
    extension: str,
) -> None:
    """
    Background task to process upload after saving

    This runs after the API returns to the user
    Handles thumbnail generation and prepares for AI processing
    """
    try:
        # Generate thumbnail
        thumbnail_path = await storage_service.generate_thumbnail(
            user_id = user_id,
            upload_id = upload_id,
            file_type = file_type,
            extension = extension,
        )

        if thumbnail_path:
            # Update upload record with thumbnail
            upload = await Upload.find_by_id(upload_id)
            if upload:
                await upload.update_thumbnail(thumbnail_path)

        # Queue for AI processing
        logger.info(f"Starting AI processing for upload {upload_id}")
        await local_ai_service.analyze_media(upload_id)
        logger.info(f"AI processing completed for upload {upload_id}")

    except Exception as e:
        logger.error(
            f"Background processing failed for upload {upload_id}: {e}"
        )
        try:
            upload = await Upload.find_by_id(upload_id)
            if upload and upload.processing_status not in [
                    ProcessingStatus.COMPLETED,
                    ProcessingStatus.FAILED
            ]:
                await upload.update_status(
                    ProcessingStatus.FAILED,
                    error_message = f"Processing failed: {str(e)[:200]}",
                )
        except Exception as update_error:
            logger.error(
                f"Failed to update status for {upload_id}: {update_error}"
            )


@router.post(
    "",
    response_model = UploadResponse,
    status_code = status.HTTP_201_CREATED,
    summary = "Upload a file",
    description = "Upload an image or video file for processing",
)
@limiter.limit(config.settings.rate_limit_upload)
async def upload_file(
    request: Request,
    file: Annotated[UploadFile,
                    File(description = "File to upload")],
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> UploadResponse:
    """
    Upload a new file

    File is saved immediately and processing happens in background
    Returns upload details with 'pending' status
    """
    # Generate upload ID early
    upload_id = uuid4()

    try:
        file_content = await file.read()
        file_size = len(file_content)

        # Reset file position for saving
        await file.seek(0)

        file_type, extension = await storage_service.validate_file(
            filename=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            file_size=file_size,
        )

        file_path = await storage_service.save_upload(
            file_content = file.file,
            user_id = current_user.id,
            upload_id = upload_id,
            extension = extension,
        )

        upload = await Upload.create(
            user_id = current_user.id,
            filename = file.filename or f"upload.{extension}",
            file_path = file_path,
            file_type = file_type,
            file_size = file_size,
            mime_type = file.content_type or "application/octet-stream",
            metadata = {
                "original_filename": file.filename,
                "upload_source": "web",
            },
            upload_id = upload_id,
        )

        # Queue background processing (fire and forget)
        task = asyncio.create_task(
            process_upload_background(
                upload_id = upload_id,
                user_id = current_user.id,
                file_type = file_type,
                extension = extension,
            )
        )
        # Store reference to prevent task from being garbage collected
        task.add_done_callback(lambda t: t.exception())

        logger.info(f"User {current_user.id} uploaded file {upload.id}")
        return UploadResponse.model_validate(upload)

    except StorageError as e:
        logger.error(f"Storage error during upload: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        with contextlib.suppress(Exception):
            await storage_service.delete_upload(current_user.id, upload_id)
        raise


@router.get(
    "",
    response_model = PaginatedResponse[UploadResponse],
    summary = "List uploads",
    description =
    "Get paginated list of user's uploads with optional filters",
)
async def list_uploads(
    current_user: Annotated[User,
                            Depends(get_current_user)],
    params: Annotated[UploadListParams,
                      Depends()],
) -> PaginatedResponse[UploadResponse]:
    """
    List user's uploads with pagination and filters

    Supports filtering by:
    - file_type: 'image' or 'video'
    - processing_status: 'pending', 'analyzing', 'embedding', 'completed', 'failed'
    - sort_by: 'created_at', 'updated_at', 'file_size', 'filename'
    - sort_order: 'asc' or 'desc'
    """
    uploads = await Upload.find_by_user(
        user_id = current_user.id,
        limit = params.limit,
        offset = params.offset,
        file_type = params.file_type,
        status = params.processing_status,
        show_hidden = params.show_hidden,
        sort_by = params.sort_by,
        sort_order = params.sort_order,
    )

    filters: dict[str, Any] = {"user_id": current_user.id}
    if params.file_type:
        filters["file_type"] = params.file_type
    if params.processing_status:
        filters["processing_status"] = params.processing_status

    total = await Upload.count(filters)

    upload_responses = [
        UploadResponse.model_validate(upload) for upload in uploads
    ]

    return PaginatedResponse[UploadResponse].create(
        items = upload_responses,
        total = total,
        page = params.page,
        page_size = params.page_size,
    )


@router.get(
    "/{upload_id}",
    response_model = UploadResponse,
    summary = "Get upload details",
    description = "Get details of a specific upload",
)
async def get_upload(
    upload: Annotated[Upload,
                      Depends(verify_upload_ownership)],
) -> UploadResponse:
    """
    Get details of a specific upload
    """
    return UploadResponse.model_validate(upload)


@router.delete(
    "/{upload_id}",
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Delete upload",
    description = "Delete an upload and all associated files",
)
async def delete_upload(
    upload: Annotated[Upload,
                      Depends(verify_upload_ownership)],
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> None:
    """
    Delete an upload and all associated files

    Removes:
    - Database record
    - Original file
    - Thumbnail
    - Any extracted frames
    """
    try:
        await storage_service.delete_upload(current_user.id, upload.id)
        await upload.delete()
        logger.info(f"User {current_user.id} deleted upload {upload.id}")
    except Exception as e:
        logger.error(f"Failed to delete upload {upload.id}: {e}")
        raise


@router.get(
    "/{upload_id}/metadata",
    summary = "Get upload metadata",
    description = "Get additional metadata extracted from file",
    response_model = dict,
)
async def get_upload_metadata(
    upload: Annotated[Upload,
                      Depends(verify_upload_ownership)],
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> dict:
    """
    Get additional metadata for upload

    Returns dimensions, format, duration (for videos), etc
    """
    metadata = await storage_service.get_upload_metadata(
        current_user.id,
        upload.id
    )

    if not metadata:
        raise NotFoundError("Metadata not available")

    return metadata


@router.patch(
    "/{upload_id}/hide",
    response_model = UploadResponse,
    summary = "Toggle upload hidden status",
    description = "Hide or unhide an upload from the gallery",
)
async def toggle_upload_hidden(
    upload: Annotated[Upload,
                      Depends(verify_upload_ownership)],
    current_user: Annotated[User,
                            Depends(get_current_user)],
    hidden: bool = True,
) -> UploadResponse:
    """
    Toggle hidden status for an upload

    Args:
        upload_id: Upload's ID
        hidden: Set to true to hide, false to unhide
    """
    await upload.update_hidden(hidden)
    logger.info(
        f"User {current_user.id} {'hid' if hidden else 'unhid'} upload {upload.id}"
    )

    return UploadResponse.model_validate(upload)


@router.post(
    "/bulk/delete",
    status_code = status.HTTP_200_OK,
    summary = "Bulk delete uploads",
    description = "Delete multiple uploads at once",
)
async def bulk_delete_uploads(
    upload_ids: list[UUID],
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> dict:
    """
    Delete multiple uploads at once
    """
    if not upload_ids:
        raise ValidationError("No upload IDs provided")

    if len(upload_ids) > config.MAX_BULK_UPLOAD_DELETE:
        raise ValidationError(
            f"Maximum {config.MAX_BULK_UPLOAD_DELETE} uploads can be deleted at once"
        )

    # Delete files from storage
    for upload_id in upload_ids:
        try:
            await storage_service.delete_upload(current_user.id, upload_id)
        except Exception as e:
            logger.warning(f"Failed to delete files for {upload_id}: {e}")

    # Delete from database
    deleted_count = await Upload.bulk_delete(upload_ids, current_user.id)
    logger.info(
        f"User {current_user.id} bulk deleted {deleted_count} uploads"
    )

    return {"deleted": deleted_count}


@router.post(
    "/bulk/hide",
    status_code = status.HTTP_200_OK,
    summary = "Bulk hide/unhide uploads",
    description = "Hide or unhide multiple uploads at once",
)
async def bulk_hide_uploads(
    upload_ids: list[UUID],
    current_user: Annotated[User,
                            Depends(get_current_user)],
    hidden: bool = True,
) -> dict:
    """
    Hide or unhide multiple uploads at once
    """
    if not upload_ids:
        raise ValidationError("No upload IDs provided")

    if len(upload_ids) > config.MAX_BULK_UPLOAD_UPDATE:
        raise ValidationError(
            f"Maximum {config.MAX_BULK_UPLOAD_UPDATE} uploads can be updated at once"
        )

    updated_count = await Upload.bulk_update_hidden(
        upload_ids,
        current_user.id,
        hidden
    )
    logger.info(
        f"User {current_user.id} bulk {'hid' if hidden else 'unhid'} {updated_count} uploads"
    )

    return {"updated": updated_count}


@router.post(
    "/{upload_id}/regenerate-description",
    response_model = UploadResponse,
    status_code = status.HTTP_200_OK,
    summary = "Regenerate AI description",
    description = "Re-run AI analysis to generate new description and embedding",
)
@limiter.limit(config.settings.rate_limit_upload)
async def regenerate_description(
    request: Request,
    upload: Annotated[Upload,
                      Depends(verify_upload_ownership)],
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> UploadResponse:
    """
    Regenerate AI generated description for an upload
    """
    await regenerate_upload_description(upload)

    logger.info(
        f"User {current_user.id} regenerated description for upload {upload.id} "
        f"(attempt #{upload.regeneration_count})"
    )

    return UploadResponse.model_validate(upload)
    
