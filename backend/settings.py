"""
Application-wide settings and constants.

Centralized location for configuration that doesn't come from environment variables.
---
/backend/settings.py
"""

from typing import Final

from passlib.context import CryptContext

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=14)

# Password validation constants
MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 69

# Embedding configuration
EMBEDDING_DIMENSIONS: Final[int] = 1536  # OpenAI text-embedding-3-small dimensions

# Special characters for password validation
SPECIAL_CHARACTERS: Final[str] = "!@#$%^&*()_+-=[]{}|;:,.<>?"

# File processing constants
THUMBNAIL_QUALITY: Final[int] = 85  # JPEG quality for thumbnails
VIDEO_SAMPLE_FPS: Final[float] = 1.0  # Extract 1 frame per second for video analysis
MAX_VIDEO_FRAMES: Final[int] = 10  # Maximum frames to extract from video

# Pagination defaults
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Cache TTL (Time To Live) in seconds
SEARCH_CACHE_TTL: Final[int] = 300  # 5 minutes for search results
USER_CACHE_TTL: Final[int] = 60  # 1 minute for user data
UPLOAD_COUNT_CACHE_TTL: Final[int] = 30  # 30 seconds for upload counts

# API Rate limiting (requests per minute)
UPLOAD_RATE_LIMIT: Final[int] = 10  # 10 uploads per minute per user
SEARCH_RATE_LIMIT: Final[int] = 60  # 60 searches per minute per user

# Processing queue settings
PROCESSING_BATCH_SIZE: Final[int] = 5  # Process 5 uploads at a time
PROCESSING_RETRY_ATTEMPTS: Final[int] = 3  # Retry failed processing 3 times
