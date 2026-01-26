"""
ⒸAngelaMos | 2026
search.py
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from config import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_QUERY_LENGTH,
    SEARCH_DEFAULT_SIMILARITY_THRESHOLD,
    SIMILAR_UPLOADS_DEFAULT_LIMIT,
    SIMILAR_UPLOADS_SIMILARITY_THRESHOLD,
)
from models.Upload import FileType
from schemas.upload import UploadResponse


class SearchRequest(BaseModel):
    """
    Semantic search request with advanced filtering options
    """
    model_config = ConfigDict(
        extra = "forbid",
        str_strip_whitespace = True,
    )

    query: str = Field(
        description = "Natural language search query",
        min_length = 1,
        max_length = MAX_QUERY_LENGTH,
    )

    limit: int = Field(
        default = DEFAULT_PAGE_SIZE,
        ge = 1,
        le = MAX_PAGE_SIZE,
        description = "Maximum number of results"
    )

    similarity_threshold: float = Field(
        default = SEARCH_DEFAULT_SIMILARITY_THRESHOLD,
        ge = 0.0,
        le = 1.0,
        description = "Minimum similarity score (0-1)"
    )

    file_types: list[FileType] | None = Field(
        default = None,
        description = "Filter by file types (None = all types)"
    )

    date_from: datetime | None = Field(
        default = None,
        description = "Filter uploads created after this date"
    )

    date_to: datetime | None = Field(
        default = None,
        description = "Filter uploads created before this date"
    )

    user_id: UUID | None = Field(
        default = None,
        description =
        "Search only within specific user's uploads (admin feature)",
    )

    @field_validator("query")
    @classmethod
    def clean_query(cls, v: str) -> str:
        """
        Clean and validate search query.
        """
        cleaned = " ".join(v.split())

        if not cleaned:
            raise ValueError("Query cannot be empty after cleaning")

        return cleaned

    @field_validator("date_to")
    @classmethod
    def validate_date_range(
        cls,
        v: datetime | None,
        info: ValidationInfo
    ) -> datetime | None:
        """
        Ensure date_to is after date_from if both provided
        """
        if v is not None and "date_from" in info.data:
            date_from = info.data["date_from"]
            if date_from is not None and v <= date_from:
                raise ValueError("date_to must be after date_from")
        return v


class SearchResult(BaseModel):
    """
    Individual search result with similarity score
    """
    model_config = ConfigDict(
        extra = "forbid",
        from_attributes = True,
    )

    upload: UploadResponse = Field(description = "Matched upload")
    similarity_score: float = Field(
        ge = 0.0,
        le = 1.0,
        description = "Similarity score (0-1, higher is more similar)"
    )
    distance: float = Field(
        ge = 0.0,
        description = "Vector distance (lower is more similar)"
    )
    rank: int = Field(
        ge = 1,
        description = "Result rank (1 is best match)"
    )


class SearchResponse(BaseModel):
    """
    Search response with results and metadata
    """
    model_config = ConfigDict(
        extra = "forbid",
    )

    results: list[SearchResult] = Field(
        description = "Search results ordered by similarity"
    )

    total_found: int = Field(
        ge = 0,
        description = "Total number of matching results"
    )

    returned_count: int = Field(
        ge = 0,
        description = "Number of results returned (may be less than limit)"
    )

    search_time_ms: float = Field(
        ge = 0,
        description = "Search execution time in milliseconds"
    )

    query: str = Field(description = "Original search query")

    query_embedding_generated: bool = Field(
        default = True,
        description = "Whether embedding was successfully generated"
    )

    applied_filters: dict[str,
                          Any] | None = Field(
                              default = None,
                              description = "Filters that were applied"
                          )


class SimilarUploadsRequest(BaseModel):
    """
    Find uploads similar to a specific upload
    """
    model_config = ConfigDict(
        extra = "forbid",
    )

    upload_id: UUID = Field(
        description = "Upload ID to find similar items for"
    )

    limit: int = Field(
        default = SIMILAR_UPLOADS_DEFAULT_LIMIT,
        ge = 1,
        le = 50,
        description = "Maximum number of similar items"
    )

    similarity_threshold: float = Field(
        default = SIMILAR_UPLOADS_SIMILARITY_THRESHOLD,
        ge = 0.0,
        le = 1.0,
        description = "Minimum similarity score"
    )

    include_same_user: bool = Field(
        default = True,
        description = "Include uploads from same user"
    )


class SearchHistoryItem(BaseModel):
    """
    Search history entry
    """
    model_config = ConfigDict(
        extra = "forbid",
        from_attributes = True,
    )

    id: UUID = Field(description = "Search history ID")
    query: str = Field(description = "Search query")
    result_count: int = Field(
        ge = 0,
        description = "Number of results found"
    )
    searched_at: datetime = Field(
        description = "When search was performed"
    )
    filters_applied: dict[str,
                          Any] | None = Field(
                              description = "Filters used in search"
                          )

