"""
ⒸAngelaMos | 2026
exceptions.py
"""

from typing import Any


class BaseAppException(Exception):
    """
    Base exception class for all application exceptions
    All custom exceptions should inherit from this
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        **kwargs: Any
    ):
        self.message = message
        self.status_code = status_code
        self.extra = kwargs
        super().__init__(self.message)


class StorageError(BaseAppException):
    """
    Base exception for storage operations
    """
    def __init__(
        self,
        message: str = "Storage operation failed",
        **kwargs: Any
    ):
        super().__init__(message, status_code = 500, **kwargs)


class FileTooLargeError(StorageError):
    """
    Raised when uploaded file exceeds size limit
    """
    def __init__(self, message: str = "File too large", **kwargs: Any):
        super().__init__(message, status_code = 413, **kwargs)


class UnsupportedFileTypeError(StorageError):
    """
    Raised when file type is not supported
    """
    def __init__(
        self,
        message: str = "Unsupported file type",
        **kwargs: Any
    ):
        super().__init__(message, status_code = 415, **kwargs)


class LocalAIError(BaseAppException):
    """
    Base exception for local AI service errors
    """
    def __init__(self, message: str = "AI service error", **kwargs: Any):
        super().__init__(message, status_code = 500, **kwargs)


class VisionError(LocalAIError):
    """
    Raised when Qwen2.5-VL inference fails
    """
    def __init__(
        self,
        message: str = "Vision analysis failed",
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)


class EmbeddingError(LocalAIError):
    """
    Raised when bge-m3 embedding fails
    """
    def __init__(
        self,
        message: str = "Embedding generation failed",
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)


class SearchServiceError(BaseAppException):
    """
    Base exception for search service errors
    """
    def __init__(
        self,
        message: str = "Search service error",
        **kwargs: Any
    ):
        super().__init__(message, status_code = 500, **kwargs)


class QueryEmbeddingError(SearchServiceError):
    """
    Raised when query embedding generation fails
    """
    def __init__(
        self,
        message: str = "Query embedding generation failed",
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)


class AuthenticationError(BaseAppException):
    """
    Raised when authentication fails
    """
    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs: Any
    ):
        super().__init__(message, status_code = 401, **kwargs)


class AuthorizationError(BaseAppException):
    """
    Raised when user is not authorized to perform an action
    """
    def __init__(self, message: str = "Not authorized", **kwargs: Any):
        super().__init__(message, status_code = 403, **kwargs)


class NotFoundError(BaseAppException):
    """
    Raised when a resource is not found
    """
    def __init__(self, message: str = "Resource not found", **kwargs: Any):
        super().__init__(message, status_code = 404, **kwargs)


class ValidationError(BaseAppException):
    """
    Raised when validation fails.
    """
    def __init__(self, message: str = "Validation failed", **kwargs: Any):
        super().__init__(message, status_code = 422, **kwargs)


class ConflictError(BaseAppException):
    """
    Raised when there is a conflict (e.g., duplicate resource)
    """
    def __init__(self, message: str = "Resource conflict", **kwargs: Any):
        super().__init__(message, status_code = 409, **kwargs)


class RateLimitExceeded(BaseAppException):
    """
    Raised when rate limit is exceeded
    """
    def __init__(
        self,
        message: str = "Calm down a little bit...",
        retry_after: int | None = None,
        **kwargs: Any
    ):
        super().__init__(message, status_code = 420, **kwargs)
        self.retry_after = retry_after
