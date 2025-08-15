"""
Upload routes for file uploads and management.

Implements async file upload with immediate response and background processing.
Follows MVP pattern: availability > security, simple but scalable.
---
/backend/routers/upload.py
"""

import asyncio
import contextlib
import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_current_user
from models import (
    ProcessingStatus,
    Upload,
    User,
)
from schemas import (
    PaginatedResponse,
    UploadListParams,
    UploadResponse,
)
from services import (
    FileTooLargeError,
    StorageError,
    UnsupportedFileTypeError,
    ai_service,
    storage_service,
)

logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/uploads",
    tags=["uploads"],
    responses={
        401: {"description": "Unauthorized"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported media type"},
        429: {"description": "Too many requests"},
    },
)


async def process_upload_background(
    upload_id: UUID,
    user_id: UUID,
    file_type: str,
    extension: str,
) -> None:
    """
    Background task to process upload after saving.

    This runs after the API returns to the user.
    Handles thumbnail generation and prepares for AI processing.
    """
    try:
        # Generate thumbnail
        thumbnail_path = await storage_service.generate_thumbnail(
            user_id=user_id,
            upload_id=upload_id,
            file_type=file_type,
            extension=extension,
        )

        if thumbnail_path:
            # Update upload record with thumbnail
            upload = await Upload.find_by_id(upload_id)
            if upload:
                await upload.update_thumbnail(thumbnail_path)

        # Queue for AI processing
        logger.info(f"Starting AI processing for upload {upload_id}")
        await ai_service.analyze_media(upload_id)
        logger.info(f"AI processing completed for upload {upload_id}")

    except Exception as e:
        logger.error(f"Background processing failed for upload {upload_id}: {e}")
        try:
            upload = await Upload.find_by_id(upload_id)
            if upload and upload.processing_status not in ["completed", "failed"]:
                await upload.update_status(
                    ProcessingStatus.FAILED,
                    error_message=f"Processing failed: {str(e)[:200]}",
                )
        except Exception as update_error:
            logger.error(f"Failed to update status for {upload_id}: {update_error}")


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description="Upload an image or video file for processing",
)
@limiter.limit("100/minute")
async def upload_file(
    request: Request,
    file: Annotated[UploadFile, File(description="File to upload")],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UploadResponse:
    """
    Upload a new file.

    File is saved immediately and processing happens in background.
    Returns upload details with 'pending' status.
    """
    # Generate upload ID early
    upload_id = uuid4()

    try:
        file_content = await file.read()
        file_size = len(file_content)

        # Reset file position for saving
        await file.seek(0)

        try:
            file_type, extension = await storage_service.validate_file(
                filename=file.filename or "unknown",
                mime_type=file.content_type or "application/octet-stream",
                file_size=file_size,
            )
        except FileTooLargeError as err:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {storage_service.base_path} bytes",
            ) from err
        except UnsupportedFileTypeError as e:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(e),
            ) from e

        file_path = await storage_service.save_upload(
            file_content=file.file,
            user_id=current_user.id,
            upload_id=upload_id,
            extension=extension,
        )

        upload = await Upload.create(
            user_id=current_user.id,
            filename=file.filename or f"upload.{extension}",
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            metadata={
                "original_filename": file.filename,
                "upload_source": "web",
            },
            upload_id=upload_id,
        )

        # Queue background processing (fire and forget)
        task = asyncio.create_task(
            process_upload_background(
                upload_id=upload_id,
                user_id=current_user.id,
                file_type=file_type,
                extension=extension,
            )
        )
        # Store reference to prevent task from being garbage collected
        task.add_done_callback(lambda t: t.exception())

        logger.info(f"User {current_user.id} uploaded file {upload.id}")
        return UploadResponse.model_validate(upload)

    except HTTPException:
        raise
    except StorageError as e:
        logger.error(f"Storage error during upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save upload",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        with contextlib.suppress(Exception):
            await storage_service.delete_upload(current_user.id, upload_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        ) from e


@router.get(
    "",
    response_model=PaginatedResponse[UploadResponse],
    summary="List uploads",
    description="Get paginated list of user's uploads with optional filters",
)
async def list_uploads(
    current_user: Annotated[User, Depends(get_current_user)],
    params: Annotated[UploadListParams, Depends()],
) -> PaginatedResponse[UploadResponse]:
    """
    List user's uploads with pagination and filters.

    Supports filtering by:
    - file_type: 'image' or 'video'
    - processing_status: 'pending', 'analyzing', 'embedding', 'completed', 'failed'
    - sort_by: 'created_at', 'updated_at', 'file_size', 'filename'
    - sort_order: 'asc' or 'desc'
    """
    # Get uploads from db
    uploads = await Upload.find_by_user(
        user_id=current_user.id,
        limit=params.limit,
        offset=params.offset,
        file_type=params.file_type,
        status=params.processing_status,
    )

    filters = {"user_id": current_user.id}
    if params.file_type:
        filters["file_type"] = params.file_type
    if params.processing_status:
        filters["processing_status"] = params.processing_status

    total = await Upload.count(filters)

    # Convert to response models
    upload_responses = [UploadResponse.model_validate(upload) for upload in uploads]

    return PaginatedResponse[UploadResponse].create(
        items=upload_responses,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/{upload_id}",
    response_model=UploadResponse,
    summary="Get upload details",
    description="Get details of a specific upload",
)
async def get_upload(
    upload_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
) -> UploadResponse:
    """
    Get details of a specific upload.

    Returns 404 if upload not found or doesn't belong to user.
    """
    upload = await Upload.find_by_id(upload_id)

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    if upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    return UploadResponse.model_validate(upload)


@router.delete(
    "/{upload_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete upload",
    description="Delete an upload and all associated files",
)
async def delete_upload(
    upload_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete an upload and all associated files.

    Removes:
    - Database record
    - Original file
    - Thumbnail
    - Any extracted frames
    """
    upload = await Upload.find_by_id(upload_id)

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    if upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    try:
        await storage_service.delete_upload(current_user.id, upload_id)

        await upload.delete()

        logger.info(f"User {current_user.id} deleted upload {upload_id}")

    except Exception as e:
        logger.error(f"Failed to delete upload {upload_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete upload",
        ) from e


@router.get(
    "/{upload_id}/metadata",
    summary="Get upload metadata",
    description="Get additional metadata extracted from file",
    response_model=dict,
)
async def get_upload_metadata(
    upload_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Get additional metadata for upload.

    Returns dimensions, format, duration (for videos), etc.
    """
    upload = await Upload.find_by_id(upload_id)

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    if upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    metadata = await storage_service.get_upload_metadata(current_user.id, upload_id)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not available",
        )

    return metadata
