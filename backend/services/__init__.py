"""
Services package for business logic.
---
/backend/services/__init__.py
"""

from .local_ai import (
    LocalAIService,
    LocalAIError,
    VisionError,
    EmbeddingError,
    local_ai_service,
)
from .storage_service import (
    FileTooLargeError,
    StorageError,
    StorageService,
    UnsupportedFileTypeError,
    storage_service,
)
from .search_service import (
    SearchService,
    SearchServiceError,
    QueryEmbeddingError,
    search_service,
)

__all__ = [

    # Storage Service
    "StorageService",
    "StorageError",
    "FileTooLargeError",
    "UnsupportedFileTypeError",
    "storage_service",

    # Local AI Service
    "LocalAIService",
    "LocalAIError",
    "VisionError",
    "EmbeddingError",
    "local_ai_service",

    # Search Service
    "SearchService",
    "SearchServiceError",
    "QueryEmbeddingError",
    "search_service",
]
