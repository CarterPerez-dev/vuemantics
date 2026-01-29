"""
ⒸAngelaMos | 2026
UploadBatch.py
"""

from __future__ import annotations

from typing import Any
from datetime import datetime
from uuid import UUID, uuid4

import config
import database
from models.Base import BaseModel


class BatchStatus:
    """
    Batch processing status constants
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UploadBatch(BaseModel):
    """
    Tracks batches of uploads for bulk processing

    Design for robustness:
    - Database is source of truth (worker crash = resume from DB)
    - Sequential processing (one at a time due to compute limits)
    - Non blocking failures (one bad upload doesn't stop batch)
    - Retry once per upload (fails twice = permanent failure)
    - WebSocket progress updates for real-time tracking
    - MCP-friendly status queries
    """
    __tablename__ = "upload_batches"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize upload batch instance
        """
        super().__init__(**kwargs)

        self.id: UUID = kwargs.get("id") or uuid4()
        self.user_id: UUID = kwargs["user_id"]
        self.status: str = kwargs.get("status", BatchStatus.PENDING)
        self.total_uploads: int = kwargs.get("total_uploads", 0)
        self.processed_uploads: int = kwargs.get("processed_uploads", 0)
        self.successful_uploads: int = kwargs.get("successful_uploads", 0)
        self.failed_uploads: int = kwargs.get("failed_uploads", 0)
        self.error_message: str | None = kwargs.get("error_message")
        self.started_at: datetime | None = kwargs.get("started_at")
        self.completed_at: datetime | None = kwargs.get("completed_at")

    @classmethod
    async def create_table(cls) -> None:
        """
        Create upload_batches table with indexes
        """
        query = """
            CREATE TABLE IF NOT EXISTS upload_batches (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                -- Status
                status VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),

                -- Progress counters
                total_uploads INTEGER NOT NULL DEFAULT 0,
                processed_uploads INTEGER NOT NULL DEFAULT 0,
                successful_uploads INTEGER NOT NULL DEFAULT 0,
                failed_uploads INTEGER NOT NULL DEFAULT 0,

                -- Error tracking
                error_message TEXT,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_upload_batches_user_id ON upload_batches(user_id);
            CREATE INDEX IF NOT EXISTS idx_upload_batches_status ON upload_batches(status);
            CREATE INDEX IF NOT EXISTS idx_upload_batches_created_at ON upload_batches(created_at DESC);
        """

        await database.db.execute(query)

    @classmethod
    async def create(
        cls,
        user_id: UUID,
        total_uploads: int,
    ) -> UploadBatch:
        """
        Create a new upload batch

        Args:
            user_id: Owner's user ID
            total_uploads: Total number of uploads in this batch

        Returns:
            Created UploadBatch instance
        """
        await cls.ensure_table_exists()

        query = """
            INSERT INTO upload_batches (
                user_id, total_uploads
            )
            VALUES ($1, $2)
            RETURNING *
        """

        record = await database.db.fetchrow(query, user_id, total_uploads)

        if record is None:
            raise ValueError("Failed to create upload batch")

        batch = cls.from_record(record)
        if batch is None:
            raise ValueError("Failed to create batch from record")

        return batch

    @classmethod
    async def find_by_user(
        cls,
        user_id: UUID,
        limit: int = config.DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> list[UploadBatch]:
        """
        Find batches for a user

        Args:
            user_id: User's ID
            limit: Maximum results
            offset: Skip N results

        Returns:
            List of UploadBatch instances
        """
        await cls.ensure_table_exists()

        query = """
            SELECT * FROM upload_batches
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """

        records = await database.db.fetch(query, user_id, limit, offset)
        return cls.from_records(records)

    @classmethod
    async def find_pending(cls, limit: int = 10) -> list[UploadBatch]:
        """
        Find pending batches for worker to process

        Args:
            limit: Maximum batches to return

        Returns:
            List of pending UploadBatch instances
        """
        await cls.ensure_table_exists()

        query = """
            SELECT * FROM upload_batches
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT $1
        """

        records = await database.db.fetch(query, limit)
        return cls.from_records(records)

    async def update_status(
        self,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """
        Update batch status

        Args:
            status: New status (use BatchStatus constants)
            error_message: Error message if failed
        """
        if self.id is None:
            raise ValueError("Cannot update status for unsaved batch")

        query = """
            UPDATE upload_batches
            SET status = $1,
                error_message = $2,
                started_at = COALESCE(started_at, NOW()),
                completed_at = CASE WHEN $3 IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE completed_at END,
                updated_at = NOW()
            WHERE id = $4
            RETURNING updated_at, started_at, completed_at
        """

        row = await database.db.fetchrow(
            query,
            status,
            error_message,
            status,
            self.id
        )
        if row:
            self.status = status
            self.error_message = error_message
            self.updated_at = row["updated_at"]
            self.started_at = row["started_at"]
            self.completed_at = row["completed_at"]

    async def increment_progress(
        self,
        successful: bool = True,
    ) -> None:
        """
        Increment progress counters after processing an upload

        Args:
            successful: True if upload processed successfully, False if failed
        """
        if self.id is None:
            raise ValueError("Cannot update progress for unsaved batch")

        if successful:
            query = """
                UPDATE upload_batches
                SET processed_uploads = processed_uploads + 1,
                    successful_uploads = successful_uploads + 1,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING processed_uploads, successful_uploads, updated_at
            """
        else:
            query = """
                UPDATE upload_batches
                SET processed_uploads = processed_uploads + 1,
                    failed_uploads = failed_uploads + 1,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING processed_uploads, failed_uploads, updated_at
            """

        row = await database.db.fetchrow(query, self.id)
        if row:
            self.processed_uploads = row["processed_uploads"]
            if successful:
                self.successful_uploads = row["successful_uploads"]
            else:
                self.failed_uploads = row["failed_uploads"]
            self.updated_at = row["updated_at"]

    async def _insert(self) -> None:
        """
        Insert new batch record.
        """
        query = """
            INSERT INTO upload_batches (
                id, user_id, status, total_uploads, processed_uploads,
                successful_uploads, failed_uploads, error_message,
                started_at, completed_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
        """

        record = await database.db.fetchrow(
            query,
            self.id,
            self.user_id,
            self.status,
            self.total_uploads,
            self.processed_uploads,
            self.successful_uploads,
            self.failed_uploads,
            self.error_message,
            self.started_at,
            self.completed_at,
        )

        if record is None:
            raise RuntimeError("Insert query failed to return a record")
        for key, value in dict(record).items():
            setattr(self, key, value)

    async def _update(self) -> None:
        """
        Update existing batch record.
        """
        query = """
            UPDATE upload_batches
            SET user_id = $1,
                status = $2,
                total_uploads = $3,
                processed_uploads = $4,
                successful_uploads = $5,
                failed_uploads = $6,
                error_message = $7,
                started_at = $8,
                completed_at = $9,
                updated_at = NOW()
            WHERE id = $10
            RETURNING *
        """

        record = await database.db.fetchrow(
            query,
            self.user_id,
            self.status,
            self.total_uploads,
            self.processed_uploads,
            self.successful_uploads,
            self.failed_uploads,
            self.error_message,
            self.started_at,
            self.completed_at,
            self.id,
        )

        if record is None:
            raise RuntimeError(f"Update query failed for batch {self.id}")
        for key, value in dict(record).items():
            setattr(self, key, value)

    def is_complete(self) -> bool:
        """
        Check if batch has processed all uploads
        """
        return self.processed_uploads >= self.total_uploads

    def get_progress_percentage(self) -> float:
        """
        Get progress as percentage (0-100)
        """
        if self.total_uploads == 0:
            return 0.0
        return (self.processed_uploads / self.total_uploads) * 100

    def __repr__(self) -> str:
        return (
            f"<UploadBatch {self.id} status={self.status} "
            f"{self.processed_uploads}/{self.total_uploads}>"
        )
