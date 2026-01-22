"""
Upload model for managing uploaded media files.

Handles file metadata, processing states, embeddings, and vector similarity search.
Supports both images and videos with AI-generated summaries and embeddings.
---
/backend/models/Upload.py
"""

import json
import logging
from enum import Enum
from typing import Any, Literal
from uuid import UUID

import database
from models import BaseModel


logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """
    Processing status states for uploads.
    """
    PENDING = "pending"  # Just uploaded, not processed
    ANALYZING = "analyzing"  # Gemini is analyzing the media
    EMBEDDING = "embedding"  # Creating embeddings with OpenAI
    COMPLETED = "completed"  # Successfully processed
    FAILED = "failed"  # Processing failed


class FileType(str, Enum):
    """
    Supported file types.
    """
    IMAGE = "image"
    VIDEO = "video"


class Upload(BaseModel):
    """
    Upload model for media files.

    Attributes:
        id: Unique identifier (UUID)
        user_id: Owner's user ID
        filename: Original filename
        file_path: Local storage path
        file_type: 'image' or 'video'
        file_size: Size in bytes
        mime_type: MIME type of file
        processing_status: Current processing state
        gemini_summary: AI-generated description
        embedding_local: 1024-dimensional vector from bge-m3
        thumbnail_path: Path to generated thumbnail
        error_message: Error details if processing failed
        metadata: Additional file metadata (JSON)
        created_at: Upload timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "uploads"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize upload instance.
        """
        super().__init__(**kwargs)
        self.user_id: UUID = kwargs.get("user_id")
        self.filename: str = kwargs.get("filename", "")
        self.file_path: str = kwargs.get("file_path", "")
        self.file_type: str = kwargs.get("file_type", "")
        self.file_size: int = kwargs.get("file_size", 0)
        self.mime_type: str = kwargs.get("mime_type", "")
        self.processing_status: str = kwargs.get(
            "processing_status",
            ProcessingStatus.PENDING
        )
        self.gemini_summary: str | None = kwargs.get("gemini_summary")

        # Handle embedding (1024-dim from bge-m3)
        embedding_local_raw = kwargs.get("embedding_local")
        if isinstance(embedding_local_raw, str):
            try:
                if embedding_local_raw.startswith(
                        "[") and embedding_local_raw.endswith("]"):
                    self.embedding_local = list(
                        map(float,
                            embedding_local_raw[1 :-1].split(","))
                    )
                else:
                    self.embedding_local = None
            except (ValueError, AttributeError):
                self.embedding_local = None
        else:
            self.embedding_local = embedding_local_raw

        self.thumbnail_path: str | None = kwargs.get("thumbnail_path")
        self.error_message: str | None = kwargs.get("error_message")

        # Handle metadata - could be dict or JSON string from database
        metadata = kwargs.get("metadata")
        if isinstance(metadata, str):
            try:
                self.metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                self.metadata = None
        else:
            self.metadata = metadata

    @classmethod
    async def create_table(cls) -> None:
        """
        Create uploads table with vector column and indexes.
        """
        await database.db.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        query = """
            CREATE TABLE IF NOT EXISTS uploads (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                -- File information
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('image', 'video')),
                file_size BIGINT NOT NULL,
                mime_type VARCHAR(100) NOT NULL,

                -- Processing
                processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
                gemini_summary TEXT,
                embedding_local vector(1024),  -- bge-m3 embeddings

                -- Metadata
                thumbnail_path TEXT,
                error_message TEXT,
                metadata JSONB,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_uploads_user_id ON uploads(user_id);
            CREATE INDEX IF NOT EXISTS idx_uploads_processing_status ON uploads(processing_status);
            CREATE INDEX IF NOT EXISTS idx_uploads_file_type ON uploads(file_type);
            CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at DESC);
        """

        await database.db.execute(query)

        # Create vector index for similarity search (after some data exists)
        # This is deferred until we have enough data for better index building

    @classmethod
    async def create(
        cls,
        user_id: UUID,
        filename: str,
        file_path: str,
        file_type: Literal["image",
                           "video"],
        file_size: int,
        mime_type: str,
        metadata: dict[str,
                       Any] | None = None,
        upload_id: UUID | None = None,
    ) -> "Upload":
        """
        Create a new upload record.

        Args:
            user_id: Owner's user ID
            filename: Original filename
            file_path: Local storage path
            file_type: 'image' or 'video'
            file_size: Size in bytes
            mime_type: MIME type
            metadata: Optional metadata

        Returns:
            Created Upload instance
        """
        await cls.ensure_table_exists()

        if upload_id:
            query = """
                INSERT INTO uploads (
                    id, user_id, filename, file_path, file_type,
                    file_size, mime_type, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """
            record = await database.db.fetchrow(
                query,
                upload_id,
                user_id,
                filename,
                file_path,
                file_type,
                file_size,
                mime_type,
                json.dumps(metadata) if metadata is not None else None,
            )
        else:
            query = """
                INSERT INTO uploads (
                    user_id, filename, file_path, file_type,
                    file_size, mime_type, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """
            record = await database.db.fetchrow(
                query,
                user_id,
                filename,
                file_path,
                file_type,
                file_size,
                mime_type,
                json.dumps(metadata) if metadata is not None else None,
            )

        return cls.from_record(record)

    @classmethod
    async def find_by_user(
        cls,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        file_type: str | None = None,
        status: str | None = None,
    ) -> list["Upload"]:
        """
        Find uploads by user with optional filters.

        Args:
            user_id: User's ID
            limit: Maximum results
            offset: Skip N results
            file_type: Filter by file type
            status: Filter by processing status

        Returns:
            List of Upload instances
        """
        await cls.ensure_table_exists()

        conditions = ["user_id = $1"]
        params = [user_id]
        param_count = 1

        if file_type:
            param_count += 1
            conditions.append(f"file_type = ${param_count}")
            params.append(file_type)

        if status:
            param_count += 1
            conditions.append(f"processing_status = ${param_count}")
            params.append(status)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT * FROM uploads
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """

        params.extend([limit, offset])
        records = await database.db.fetch(query, *params)
        return cls.from_records(records)

    @classmethod
    async def search_by_embedding(
        cls,
        query_embedding: list[float],
        user_id: UUID | None = None,
        limit: int = 20,
        similarity_threshold: float = 0.0,
        use_local: bool = True,
    ) -> list[tuple["Upload",
                    float]]:
        """
        Search uploads by vector similarity.

        Args:
            query_embedding: Query vector (1024-dim bge-m3)
            user_id: Optional filter by user
            limit: Maximum results
            similarity_threshold: Minimum similarity score (0-1)
            use_local: If True, search embedding_local, else embedding

        Returns:
            List of (Upload, similarity_score) tuples
        """
        await cls.ensure_table_exists()

        filters = {"processing_status": ProcessingStatus.COMPLETED}
        if user_id:
            filters["user_id"] = user_id

        embedding_column = "embedding_local" if use_local else "embedding"

        records = await database.db.vector_similarity_search(
            table_name = cls.__tablename__,
            embedding_column = embedding_column,
            query_embedding = query_embedding,
            limit = limit,
            filters = filters,
        )

        results = []
        for record in records:
            upload = cls.from_record(record)
            similarity = record["similarity"]

            if similarity >= similarity_threshold:
                results.append((upload, similarity))

        return results

    @classmethod
    async def create_embedding_index(cls, lists: int = 100) -> None:
        """
        Create IVFFlat index for vector similarity search.

        Should be called after having at least 1000 uploads with embeddings.

        Args:
            lists: Number of clusters for IVFFlat index
        """
        await database.db.create_vector_index(
            table_name = cls.__tablename__,
            embedding_column = "embedding",
            index_type = "ivfflat",
            lists = lists,
        )

    async def _insert(self) -> None:
        """
        Insert new upload record.
        """
        query = """
            INSERT INTO uploads (
                user_id, filename, file_path, file_type,
                file_size, mime_type, processing_status,
                gemini_summary, embedding, thumbnail_path,
                error_message, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """

        record = await database.db.fetchrow(
            query,
            self.user_id,
            self.filename,
            self.file_path,
            self.file_type,
            self.file_size,
            self.mime_type,
            self.processing_status,
            self.gemini_summary,
            self.embedding,
            self.thumbnail_path,
            self.error_message,
            json.dumps(self.metadata)
            if self.metadata is not None else None,
        )

        for key, value in dict(record).items():
            setattr(self, key, value)

    async def _update(self) -> None:
        """
        Update existing upload record.
        """
        query = """
            UPDATE uploads
            SET filename = $1,
                file_path = $2,
                file_type = $3,
                file_size = $4,
                mime_type = $5,
                processing_status = $6,
                gemini_summary = $7,
                embedding = $8,
                thumbnail_path = $9,
                error_message = $10,
                metadata = $11,
                updated_at = NOW()
            WHERE id = $12
            RETURNING *
        """

        record = await database.db.fetchrow(
            query,
            self.filename,
            self.file_path,
            self.file_type,
            self.file_size,
            self.mime_type,
            self.processing_status,
            self.gemini_summary,
            self.embedding,
            self.thumbnail_path,
            self.error_message,
            json.dumps(self.metadata)
            if self.metadata is not None else None,
            self.id,
        )

        if record:
            for key, value in dict(record).items():
                setattr(self, key, value)

    async def update_status(
        self,
        status: ProcessingStatus,
        error_message: str | None = None
    ) -> None:
        """
        Update processing status.

        Args:
            status: New processing status
            error_message: Error message if failed
        """
        if self.id is None:
            raise ValueError("Cannot update status for unsaved upload")

        query = """
            UPDATE uploads
            SET processing_status = $1,
                error_message = $2,
                updated_at = NOW()
            WHERE id = $3
            RETURNING updated_at
        """

        updated_at = await database.db.fetchval(
            query,
            status,
            error_message,
            self.id
        )
        if updated_at:
            self.processing_status = status
            self.error_message = error_message
            self.updated_at = updated_at

    async def update_analysis(
        self,
        gemini_summary: str,
        embedding: list[float],
        use_local: bool = True
    ) -> None:
        """
        Update with AI analysis results.

        Args:
            gemini_summary: Text description from vision model
            embedding: Vector embedding (1024-dim bge-m3)
            use_local: If True, save to embedding_local (default)
        """
        if self.id is None:
            raise ValueError("Cannot update analysis for unsaved upload")

        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            embedding_list = embedding[0]
        elif isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], (int, float)):
            embedding_list = embedding
        else:
            raise ValueError(f"Invalid embedding format: {type(embedding)}")

        if use_local:
            query = """
                UPDATE uploads
                SET gemini_summary = $1,
                    embedding_local = $2,
                    processing_status = $3,
                    updated_at = NOW()
                WHERE id = $4
                RETURNING updated_at
            """
        else:
            query = """
                UPDATE uploads
                SET gemini_summary = $1,
                    embedding = $2,
                    processing_status = $3,
                    updated_at = NOW()
                WHERE id = $4
                RETURNING updated_at
            """

        updated_at = await database.db.fetchval(
            query,
            gemini_summary,
            embedding_list,
            ProcessingStatus.COMPLETED,
            self.id
        )

        if updated_at:
            self.gemini_summary = gemini_summary
            if use_local:
                self.embedding_local = embedding_list
            else:
                self.embedding = embedding_list
            self.processing_status = ProcessingStatus.COMPLETED
            self.updated_at = updated_at

    async def update_thumbnail(self, thumbnail_path: str) -> None:
        """
        Update thumbnail path.

        Args:
            thumbnail_path: Path to generated thumbnail
        """
        if self.id is None:
            raise ValueError("Cannot update thumbnail for unsaved upload")

        query = """
            UPDATE uploads
            SET thumbnail_path = $1,
                updated_at = NOW()
            WHERE id = $2
            RETURNING updated_at
        """

        updated_at = await database.db.fetchval(
            query,
            thumbnail_path,
            self.id
        )
        if updated_at:
            self.thumbnail_path = thumbnail_path
            self.updated_at = updated_at

    @classmethod
    async def get_pending_uploads(cls, limit: int = 10) -> list["Upload"]:
        """
        Get uploads that need processing.

        Args:
            limit: Maximum number to return

        Returns:
            List of uploads with pending status
        """
        await cls.ensure_table_exists()

        query = """
            SELECT * FROM uploads
            WHERE processing_status = $1
            ORDER BY created_at ASC
            LIMIT $2
        """

        records = await database.db.fetch(
            query,
            ProcessingStatus.PENDING,
            limit
        )
        return cls.from_records(records)

    @classmethod
    async def count_by_user(cls, user_id: UUID) -> dict[str, int]:
        """
        Get upload counts by status for a user.
        """
        await cls.ensure_table_exists()

        query = """
            SELECT processing_status, COUNT(*) as count
            FROM uploads
            WHERE user_id = $1
            GROUP BY processing_status
        """

        records = await database.db.fetch(query, user_id)
        return {
            record["processing_status"]: record["count"]
            for record in records
        }

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Convert to dictionary, handling embedding specially.
        """
        exclude = exclude or set()

        # Get base dict
        result = super().to_dict(exclude)

        # Don't include full embedding in API responses (too large)
        if "embedding" not in exclude and self.embedding:
            result["has_embedding"] = True
            result.pop("embedding", None)

        return result

    def __repr__(self) -> str:
        """
        String representation of Upload.
        """
        return f"<Upload id={self.id} filename={self.filename} status={self.processing_status}>"
