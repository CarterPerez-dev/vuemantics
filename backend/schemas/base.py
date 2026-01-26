"""
ⒸAngelaMos | 2026
base.py
"""

from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from config import (
    MAX_PAGE_SIZE,
    DEFAULT_PAGE_SIZE,
)


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints
    """
    model_config = ConfigDict(
        extra = "forbid",
        str_strip_whitespace = True,
    )

    page: int = Field(
        default = 1,
        ge = 1,
        description = "Page number (1-indexed)"
    )
    page_size: int = Field(
        default = DEFAULT_PAGE_SIZE,
        ge = 1,
        le = MAX_PAGE_SIZE,
        description = f"Items per page (max {MAX_PAGE_SIZE})"
    )

    @property
    def offset(self) -> int:
        """
        Calculate offset for database queries
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """
        Get limit for database queries
        """
        return self.page_size


class PaginatedResponse[T](BaseModel):
    """
    Generic paginated response wrapper
    """
    model_config = ConfigDict(
        extra = "forbid",
    )

    items: list[T] = Field(description = "List of items for current page")
    total: int = Field(ge = 0, description = "Total number of items")
    page: int = Field(ge = 1, description = "Current page number")
    page_size: int = Field(ge = 1, description = "Items per page")
    pages: int = Field(ge = 0, description = "Total number of pages")

    @classmethod
    def create(cls,
               items: list[T],
               total: int,
               page: int,
               page_size: int) -> PaginatedResponse[T]:
        """
        Create paginated response with calculated pages
        """
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return cls(
            items = items,
            total = total,
            page = page,
            page_size = page_size,
            pages = pages
        )


class TimestampMixin(BaseModel):
    """
    Mixin for models with timestamps
    """
    model_config = ConfigDict(
        extra = "forbid",
    )

    created_at: datetime = Field(description = "Creation timestamp")
    updated_at: datetime = Field(description = "Last update timestamp")

