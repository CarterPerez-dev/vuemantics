"""
Base schemas for shared components.

Provides reusable schemas like pagination
that are used across multiple endpoints.
---
/backend/schemas/base.py
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.
    """

    model_config = ConfigDict(
        extra="ignore",  # Allow extra fields for MVP
        str_strip_whitespace=True,
    )

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    )

    @property
    def offset(self) -> int:
        """
        Calculate offset for database queries.
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """
        Get limit for database queries.
        """
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.
    """

    model_config = ConfigDict(
        extra="ignore",  # Allow extra fields for MVP
    )

    items: list[T] = Field(description="List of items for current page")
    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> PaginatedResponse[T]:
        """
        Create paginated response with calculated pages.
        """
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return cls(
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )


class TimestampMixin(BaseModel):
    """
    Mixin for models with timestamps.
    """

    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ErrorResponse(BaseModel):
    """
    Standard error response.
    """

    model_config = ConfigDict(
        extra="ignore",  # Allow extra fields for MVP
    )

    detail: str = Field(description="Error message")
    code: str | None = Field(default=None, description="Error code")
    field: str | None = Field(default=None, description="Field that caused error")
