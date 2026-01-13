"""
Schemas package for request/response validation.
All Pydantic models for API request and response validation.
---
/backend/schemas/__init__.py
"""

from .base import (
    PaginationParams,
    PaginatedResponse,
    TimestampMixin,
    ErrorResponse,
)
from .auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from .user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
    PasswordChangeRequest,
    UserStats,
)
from .upload import (
    UploadResponse,
    UploadListParams,
    UploadStats,
    BulkUploadResponse,
)
from .search import (
    SearchRequest,
    SearchResult,
    SearchResponse,
    SimilarUploadsRequest,
    SearchHistoryItem,
)

__all__ = [

    # Base
    "PaginationParams",
    "PaginatedResponse",
    "TimestampMixin",
    "ErrorResponse",

    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",

    # User
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "PasswordChangeRequest",
    "UserStats",

    # Upload
    "UploadResponse",
    "UploadListParams",
    "UploadStats",
    "BulkUploadResponse",

    # Search
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    "SimilarUploadsRequest",
    "SearchHistoryItem",
]
