"""
ⒸAngelaMos | 2026
bulk_upload_service.py
"""

import logging
from uuid import UUID
from dataclasses import dataclass

from fastapi import UploadFile

import config
from core import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    NotFoundError,
    ValidationError,
)
from models.Upload import Upload
from models.UploadBatch import UploadBatch
from services.storage_service import storage_service
from workers.batch_processor import process_batch


logger = logging.getLogger(__name__)


@dataclass
class BulkUploadResult:
    """
    Result of bulk upload operation
    """
    batch_id: UUID
    total_files: int
    queued: int
    failed: int
    upload_ids: list[str]
    failed_files: list[dict[str, str]]


@dataclass
class BatchStatusResult:
    """
    Batch status information
    """
    batch_id: UUID
    status: str
    total_uploads: int
    processed_uploads: int
    successful_uploads: int
    failed_uploads: int
    progress_percentage: float
    created_at: str | None
    started_at: str | None
    completed_at: str | None
    error_message: str | None


class BulkUploadService:
    """
    Service for handling bulk upload operations

    Responsibilities:
    - Validate bulk upload requests
    - Create batch records
    - Process and save files
    - Queue batches for background processing
    - Track batch status
    """
    @staticmethod
    def _validate_bulk_upload(files: list[UploadFile]) -> None:
        """
        Validate bulk upload request

        Args:
            files: List of uploaded files

        Raises:
            ValidationError: If validation fails
        """
        if len(files) == 0:
            raise ValidationError("No files provided")

        if len(files) > config.MAX_BULK_FILES:
            raise ValidationError(
                f"Too many files. Maximum {config.MAX_BULK_FILES} files per batch"
            )

        total_size = sum(file.size or 0 for file in files)
        if total_size > config.MAX_BULK_SIZE:
            max_gb = config.MAX_BULK_SIZE / (1024 * 1024 * 1024)
            raise ValidationError(
                f"Total file size exceeds {max_gb}GB limit"
            )

    @staticmethod
    async def create_bulk_upload(
        user_id: UUID,
        files: list[UploadFile],
    ) -> BulkUploadResult:
        """
        Create and queue a bulk upload batch

        Args:
            user_id: User's UUID
            files: List of files to upload

        Returns:
            BulkUploadResult with batch info

        Process:
        1. Validate bulk upload request
        2. Create batch record
        3. Save each file to storage
        4. Create upload records linked to batch
        5. Queue batch for background processing
        6. Return batch ID and results
        """
        # Validate bulk upload
        BulkUploadService._validate_bulk_upload(files)

        total_size = sum(file.size or 0 for file in files)
        logger.info(
            f"Creating bulk upload for user {user_id}: "
            f"{len(files)} files, {total_size / (1024 * 1024):.2f} MB total"
        )

        batch = await UploadBatch.create(
            user_id = user_id,
            total_uploads = len(files),
        )

        logger.info(f"Created batch {batch.id} with {len(files)} uploads")

        upload_ids = []
        failed_files = []

        for file in files:
            try:
                if not file.filename:
                    failed_files.append(
                        {
                            "filename": "unknown",
                            "error": "No filename provided",
                        }
                    )
                    continue

                result = await storage_service.save_upload(
                    user_id = user_id,
                    file = file,
                )

                upload = await Upload.create(
                    user_id = user_id,
                    batch_id = batch.id,
                    filename = result.filename,
                    file_path = result.file_path,
                    file_type = result.file_type,
                    file_size = result.file_size,
                    mime_type = result.mime_type,
                    metadata = result.metadata,
                )

                upload_ids.append(str(upload.id))
                logger.debug(
                    f"Created upload {upload.id} in batch {batch.id}"
                )

            except (FileTooLargeError, UnsupportedFileTypeError) as e:
                logger.warning(
                    f"File validation failed for {file.filename}: {e}"
                )
                failed_files.append(
                    {
                        "filename": file.filename,
                        "error": str(e),
                    }
                )
            except Exception as e:
                logger.error(
                    f"Error processing file {file.filename}: {e}",
                    exc_info = True,
                )
                failed_files.append(
                    {
                        "filename": file.filename,
                        "error": "Internal error during file processing",
                    }
                )

        if len(upload_ids) != batch.total_uploads:
            batch.total_uploads = len(upload_ids)
            await batch.save()
            logger.info(
                f"Updated batch {batch.id} total uploads to {len(upload_ids)}"
            )

        if len(upload_ids) > 0:
            process_batch.send(str(batch.id))
            logger.info(
                f"Queued batch {batch.id} for processing ({len(upload_ids)} uploads)"
            )

        logger.info(
            f"Bulk upload completed for batch {batch.id}: "
            f"{len(upload_ids)} queued, {len(failed_files)} failed"
        )

        return BulkUploadResult(
            batch_id = batch.id,
            total_files = len(files),
            queued = len(upload_ids),
            failed = len(failed_files),
            upload_ids = upload_ids,
            failed_files = failed_files,
        )

    @staticmethod
    async def get_batch_status(
        batch_id: UUID,
        user_id: UUID,
    ) -> BatchStatusResult:
        """
        Get batch status for a user

        Args:
            batch_id: Batch UUID
            user_id: User UUID

        Returns:
            BatchStatusResult
        """
        batch = await UploadBatch.find_by_id(batch_id)

        if not batch:
            raise NotFoundError("Batch not found")

        if batch.user_id != user_id:
            raise NotFoundError("Batch not found")

        return BatchStatusResult(
            batch_id = batch.id,
            status = batch.status,
            total_uploads = batch.total_uploads,
            processed_uploads = batch.processed_uploads,
            successful_uploads = batch.successful_uploads,
            failed_uploads = batch.failed_uploads,
            progress_percentage = batch.get_progress_percentage(),
            created_at = batch.created_at.isoformat()
            if batch.created_at else None,
            started_at = batch.started_at.isoformat()
            if batch.started_at else None,
            completed_at = batch.completed_at.isoformat()
            if batch.completed_at else None,
            error_message = batch.error_message,
        )

    @staticmethod
    async def list_user_batches(
        user_id: UUID,
        limit: int = config.BATCH_LIST_DEFAULT_LIMIT,
        offset: int = config.BATCH_LIST_DEFAULT_OFFSET,
    ) -> list[BatchStatusResult]:
        """
        List batches for a user

        Args:
            user_id: User UUID
            limit: Max results
            offset: Skip N results

        Returns:
            List of BatchStatusResult
        """
        # Validate pagination parameters
        if limit < 1 or limit > config.BATCH_LIST_MAX_LIMIT:
            raise ValidationError(
                f"Limit must be between 1 and {config.BATCH_LIST_MAX_LIMIT}"
            )

        if offset < 0:
            raise ValidationError("Offset must be non-negative")

        batches = await UploadBatch.find_by_user(
            user_id = user_id,
            limit = min(limit,
                        config.BATCH_LIST_MAX_LIMIT),
            offset = offset,
        )

        return [
            BatchStatusResult(
                batch_id = batch.id,
                status = batch.status,
                total_uploads = batch.total_uploads,
                processed_uploads = batch.processed_uploads,
                successful_uploads = batch.successful_uploads,
                failed_uploads = batch.failed_uploads,
                progress_percentage = batch.get_progress_percentage(),
                created_at = batch.created_at.isoformat() if batch.created_at else None,
                started_at = None,  # Not needed for list view
                completed_at = batch.completed_at.isoformat() if batch.completed_at else None,
                error_message = None,  # Not needed for list view
            )
            for batch in batches
        ]


bulk_upload_service = BulkUploadService()
