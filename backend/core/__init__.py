"""
ⒸAngelaMos | 2026
Core package for application infrastructure.

Includes exceptions, responses, rate limiting, middleware, and validators.
"""

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    BaseAppException,
    ConflictError,
    EmbeddingError,
    FileTooLargeError,
    LocalAIError,
    NotFoundError,
    QueryEmbeddingError,
    RateLimitExceeded,
    SearchServiceError,
    StorageError,
    UnsupportedFileTypeError,
    ValidationError,
    VisionError,
)
from .rate_limit import limiter
from .responses import (
    AUTH_401,
    CONFLICT_409,
    FILE_TOO_LARGE_413,
    FORBIDDEN_403,
    NOT_FOUND_404,
    RATE_LIMIT_420,
    SERVER_ERROR_500,
    SERVICE_UNAVAILABLE_503,
    UNSUPPORTED_MEDIA_415,
    VALIDATION_422,
)
from .error_schemas import ErrorDetail
from .correlation import CorrelationIdMiddleware
from .validators import (
    hash_password,
    verify_password,
    verify_password_safe,
    validate_password_strength,
    generate_secure_token,
)


__all__ = [
    # Exceptions
    "BaseAppException",
    "StorageError",
    "FileTooLargeError",
    "UnsupportedFileTypeError",
    "LocalAIError",
    "VisionError",
    "EmbeddingError",
    "SearchServiceError",
    "QueryEmbeddingError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "RateLimitExceeded",
    # Response definitions
    "AUTH_401",
    "FORBIDDEN_403",
    "NOT_FOUND_404",
    "CONFLICT_409",
    "FILE_TOO_LARGE_413",
    "UNSUPPORTED_MEDIA_415",
    "VALIDATION_422",
    "RATE_LIMIT_420",
    "SERVER_ERROR_500",
    "SERVICE_UNAVAILABLE_503",
    # Error schemas
    "ErrorDetail",
    # Rate limiting
    "limiter",
    # Middleware
    "CorrelationIdMiddleware",
    # Validators
    "hash_password",
    "verify_password",
    "verify_password_safe",
    "validate_password_strength",
    "generate_secure_token",
]
