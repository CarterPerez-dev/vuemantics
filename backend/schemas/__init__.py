"""
ⒸAngelaMos | 2026
__init__.py
"""

from .base import (
    PaginationParams,
    PaginatedResponse,
    TimestampMixin,
)
from .common import (
    AppInfoResponse,
)
from .auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from .client_config import (
    ClientConfigResponse,
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
from .health import (
    HealthStatus,
    HealthDetailedResponse,
)

__all__ = [

    # Base
    "PaginationParams",
    "PaginatedResponse",
    "TimestampMixin",

    # Common
    "AppInfoResponse",

    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",

    # Client Config
    "ClientConfigResponse",

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

    # Health
    "HealthStatus",
    "HealthDetailedResponse",
]
