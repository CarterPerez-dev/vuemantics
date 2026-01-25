"""
ⒸAngelaMos | 2026
upload.py
"""

from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

from config import EMBEDDING_DIMENSIONS
from models.Upload import FileType, ProcessingStatus
from schemas import PaginationParams, TimestampMixin


class UploadResponse(TimestampMixin):
    """
    Upload response with all fields including embedding.

    Note: Full embedding is included for similarity calculations.
    """
    model_config = ConfigDict(
        extra = "ignore",  # Allow extra fields for MVP flexibility
        from_attributes = True,
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "filename": "vacation_photo.jpg",
                "file_path": "/storage/uploads/user123/file456/vacation_photo.jpg",
                "file_type": "image",
                "file_size": 2048576,
                "mime_type": "image/jpeg",
                "processing_status": "completed",
                "description": "A beach scene with palm trees and sunset",
                "embedding_local": [0.123, -0.456, 0.789],  # ... 1024 dimensions
                "thumbnail_path": "/storage/uploads/user123/file456/thumb_vacation_photo.jpg",
                "error_message": None,
                "metadata": {"width": 1920, "height": 1080},
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:31:00Z",
            }
        },
    )

    id: UUID = Field(description = "Upload's unique identifier")
    user_id: UUID = Field(description = "Owner's user ID")
    filename: str = Field(description = "Original filename")
    file_path: str = Field(description = "Storage path")
    file_type: FileType = Field(description = "Type of media")
    file_size: int = Field(gt = 0, description = "File size in bytes")
    mime_type: str = Field(description = "MIME type")
    processing_status: ProcessingStatus = Field(
        description = "Current processing status"
    )
    description: str | None = Field(
        default = None,
        description = "AI-generated description from vision model"
    )
    description_audit_score: int | None = Field(
        default = None,
        ge = 0,
        le = 100,
        description = "Description quality score (0-100, higher is better)"
    )
    embedding_local: list[float] | None = Field(
        default = None,
        description =
        f"{EMBEDDING_DIMENSIONS}-dimensional embedding vector from bge-m3",
        min_length = EMBEDDING_DIMENSIONS,
        max_length = EMBEDDING_DIMENSIONS,
    )
    has_embedding: bool = Field(
        default = False,
        description = "Whether this upload has an embedding generated"
    )
    thumbnail_path: str | None = Field(
        default = None,
        description = "Path to generated thumbnail"
    )
    error_message: str | None = Field(
        default = None,
        description = "Error details if processing failed"
    )
    metadata: dict[str,
                   Any] | None = Field(
                       default = None,
                       description = "Additional file metadata"
                   )
    hidden: bool = Field(
        default = False,
        description = "Whether this upload is hidden from gallery"
    )
    regeneration_count: int = Field(
        default = 0,
        ge = 0,
        description = "Number of times description was regenerated"
    )
    last_regenerated_at: str | None = Field(
        default = None,
        description = "Timestamp of last regeneration"
    )

    @field_validator("embedding_local")
    @classmethod
    def validate_embedding_dimensions(cls,
                                      v: list[float] | None
                                      ) -> list[float] | None:
        """
        Ensure embedding has exactly required dimensions.
        """
        if v is not None and len(v) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Embedding must have exactly {EMBEDDING_DIMENSIONS} dimensions, got {len(v)}"
            )
        return v

    @field_serializer("file_path")
    def serialize_file_path(self, v: str) -> str:
        """
        Prepend /files/ to relative path for nginx serving.
        """
        if v and not v.startswith("/files/"):
            return f"/files/{v}"
        return v

    @field_serializer("thumbnail_path")
    def serialize_thumbnail_path(self, v: str | None) -> str | None:
        """
        Prepend /files/ to relative thumbnail path for nginx serving.
        """
        if v and not v.startswith("/files/"):
            return f"/files/{v}"
        return v


class UploadListParams(PaginationParams):
    """
    Parameters for listing uploads with filters.
    """
    file_type: FileType | None = Field(
        default = None,
        description = "Filter by file type"
    )
    processing_status: ProcessingStatus | None = Field(
        default = None,
        description = "Filter by processing status"
    )
    sort_by: Literal["created_at",
                     "updated_at",
                     "file_size",
                     "filename"] = Field(
                         default = "created_at",
                         description = "Sort field"
                     )
    sort_order: Literal["asc",
                        "desc"] = Field(
                            default = "desc",
                            description = "Sort order"
                        )
    show_hidden: bool = Field(
        default = False,
        description = "Include hidden uploads in results"
    )


class UploadStats(BaseModel):
    """
    Upload statistics by type and status.
    """

    model_config = ConfigDict(
        extra = "ignore",  # Allow extra fields for MVP flexibility
    )

    total_count: int = Field(ge = 0, description = "Total uploads")
    total_size_bytes: int = Field(
        ge = 0,
        description = "Total size in bytes"
    )

    by_type: dict[str,
                  int] = Field(
                      description = "Counts by file type",
                      examples = [{
                          "image": 150,
                          "video": 50
                      }]
                  )
    by_status: dict[str,
                    int] = Field(
                        description = "Counts by processing status",
                        examples = [
                            {
                                "completed": 180,
                                "failed": 5,
                                "pending": 15
                            }
                        ],
                    )

    average_processing_time_seconds: float | None = Field(
        ge = 0,
        description = "Average time to process uploads"
    )


class BulkUploadResponse(BaseModel):
    """
    Response for bulk upload operations.
    """
    model_config = ConfigDict(
        extra = "ignore",  # Allow extra fields for MVP flexibility
    )

    successful: list[UploadResponse] = Field(
        description = "Successfully created uploads"
    )
    failed: list[dict[str,
                      str]
                 ] = Field(
                     description = "Failed uploads with error messages",
                     examples = [
                         [
                             {
                                 "filename": "bad.txt",
                                 "error": "Unsupported file type"
                             }
                         ]
                     ],
                 )
    total_processed: int = Field(
        ge = 0,
        description = "Total files processed"
    )
    total_successful: int = Field(
        ge = 0,
        description = "Total successful uploads"
    )
    total_failed: int = Field(ge = 0, description = "Total failed uploads")
