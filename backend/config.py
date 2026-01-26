"""
ⒸAngelaMos | 2026
config.py
"""

import warnings
from pathlib import Path
from typing import Final
from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

APP_VERSION: Final[str] = "1.0.1"

API_CONTACT: Final[dict[str,
                        str]
                   ] = {
                       "name": "AngelaMos",
                       "url":
                       "https://github.com/CarterPerez-dev/vuemantics",
                   }
API_LICENSE: Final[dict[str,
                        str]
                   ] = {
                       "name": "GNU Affero General Public License v3.0",
                       "url": "https://www.gnu.org/licenses/agpl-3.0.html",
                   }
API_DESCRIPTION: Final[str] = (
    "Semantic search API for images using local AI. "
    "Upload images, search by natural language, discover similar content. "
    "Built with FastAPI, PostgreSQL, pgvector, and Ollama."
)

OPENAPI_VERSION: Final[str] = "3.1.0"
API_ROOT_PATH: Final[str] = "/api"
API_DOCS_URL: Final[str] = "/docs"
API_REDOC_URL: Final[str] = "/redoc"
API_OPENAPI_URL: Final[str] = "/openapi.json"


# Important
# ======================================================
SEARCH_DEFAULT_SIMILARITY_THRESHOLD: Final[float] = 0.48  # Default for search queries
SIMILAR_UPLOADS_SIMILARITY_THRESHOLD: Final[float] = 0.48  # Threshold for "find similar"
# ======================================================


EMBEDDING_DIMENSIONS: Final[int] = 1024  # bge-m3 dimensions
IVFFLAT_INDEX_LISTS: Final[int] = 100  # IVFFlat clusters for pgvector

# AI Model config
OLLAMA_VISION_TEMPERATURE: Final[float] = 0.3
OLLAMA_VISION_NUM_PREDICT_IMAGE: Final[int] = 512  # Max tokens for image analysis
OLLAMA_VISION_NUM_PREDICT_VIDEO: Final[int] = 2048  # Max tokens for video analysis (videos need detailed descriptions)
OLLAMA_VISION_NUM_CTX: Final[int] = 8192  # Context window (qwen2.5vl supports up to 128K)

# Text processing limits
MAX_EMBEDDING_TEXT_LENGTH: Final[int] = 32000  # Max chars for embedding generation

# Concurrency limits
VISION_SEMAPHORE_LIMIT: Final[int] = 1  # Max concurrent vision operations
EMBEDDING_SEMAPHORE_LIMIT: Final[int] = 3  # Max concurrent embedding operations
BATCH_ANALYZE_MAX_CONCURRENT: Final[int] = 3  # Max parallel uploads in batch analysis
BATCH_EMBEDDING_MAX_CONCURRENT: Final[int] = 3  # Max parallel embedding generations

# Search configuration
SEARCH_RESULT_MULTIPLIER: Final[int] = 2  # Multiply limit for pre-filtering
BATCH_SEARCH_MAX_CONCURRENT: Final[int] = 3  # Max parallel searches in batch
BATCH_SEARCH_DEFAULT_LIMIT: Final[int] = 10  # Default results per query in batch
SIMILAR_UPLOADS_DEFAULT_LIMIT: Final[int] = 6  # Default similar uploads to return
SEARCH_SUGGESTIONS_DEFAULT_LIMIT: Final[int] = 5  # Default search suggestions to return

# Processing queue settings
PROCESSING_BATCH_SIZE: Final[int] = 5  # Process 5 uploads at a time
PROCESSING_RETRY_ATTEMPTS: Final[int] = 3  # Retry failed processing 3 times
PENDING_UPLOADS_LIMIT: Final[int] = 10  # Max pending uploads to fetch for processing

# File processing constants
THUMBNAIL_QUALITY: Final[int] = 85  # JPEG
THUMBNAIL_FILENAME: Final[str] = "thumb_256.jpg"
VIDEO_SAMPLE_FPS: Final[float] = 1.0  # Extract 1 frame per second for video analysis
MAX_VIDEO_FRAMES: Final[int] = 10  # Maximum frames to extract from video
MAX_VIDEO_FRAMES_FOR_ANALYSIS: Final[int] = 10  # Maximum frames to send to vision model (8K context is plenty)

# Description audit configuration
DESCRIPTION_MIN_LENGTH: Final[int] = 50
DESCRIPTION_MAX_LENGTH: Final[int] = 5000
DESCRIPTION_MIN_WORD_DIVERSITY: Final[float] = 0.20  # 20% unique words minimum
DESCRIPTION_MAX_CONSECUTIVE_REPEATS: Final[int] = 3  # Flag if 4+ same words in a row
DESCRIPTION_MAX_GIBBERISH_RATIO: Final[float] = 0.30  # 30% non alpha max
DESCRIPTION_AUDIT_PASS_THRESHOLD: Final[int] = 60  # Score must be >= 60 to pass

# Audit penalties (deducted from 100)
AUDIT_PENALTY_BAD_TOKEN: Final[int] = 50
AUDIT_PENALTY_TOO_SHORT: Final[int] = 30
AUDIT_PENALTY_TOO_LONG: Final[int] = 20
AUDIT_PENALTY_LOW_DIVERSITY: Final[int] = 40
AUDIT_PENALTY_CONSECUTIVE_REPEATS: Final[int] = 35
AUDIT_PENALTY_HIGH_GIBBERISH: Final[int] = 25




FILE_UPLOAD_CHUNK_SIZE: Final[int] = 1024 * 1024  # 1MB

DEFAULT_PAGE_SIZE: Final[int] = 50
MAX_PAGE_SIZE: Final[int] = 100
DEFAULT_QUERY_LIMIT: Final[int] = 100  # Default limit for db queries

SEARCH_CACHE_TTL: Final[int] = 300  # 5 minutes
USER_CACHE_TTL: Final[int] = 60  # 1 minute
UPLOAD_COUNT_CACHE_TTL: Final[int] = 30  # seconds

MIN_QUERY_LENGTH: Final[int] = 1
MAX_QUERY_LENGTH: Final[int] = 500

MAX_BULK_UPLOAD_DELETE: Final[int] = 100
MAX_BULK_UPLOAD_UPDATE: Final[int] = 100

BCRYPT_ROUNDS: Final[int] = 14  # salt rounds

ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 30

MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 72  # bcrypt max
SPECIAL_CHARACTERS: Final[str] = "!@#$%^&*()_+-=[]{}|;:,.<>?"

WEBSOCKET_AUTH_TIMEOUT: Final[float] = 5.0  # Seconds to wait for auth message
WEBSOCKET_HEARTBEAT_INTERVAL: Final[int] = 30  # Seconds between heartbeats
WEBSOCKET_CLOSE_AUTH_TIMEOUT: Final[int] = 4001  # Close code for auth timeout
WEBSOCKET_CLOSE_AUTH_REQUIRED: Final[int] = 4002  # Close code for missing auth
WEBSOCKET_CLOSE_INVALID_TOKEN: Final[int] = 4003  # Close code for invalid token
WEBSOCKET_CLOSE_INVALID_MESSAGE: Final[int] = 4004  # Close code for invalid message format


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    model_config = SettingsConfigDict(
        env_file = _ENV_FILE,
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore",
    )

    app_name: str = Field(
        default = "Vuemantics",
        description = "Application name"
    )
    environment: str = Field(
        default = "development",
        description = "Runtime environment",
    )
    debug: bool = Field(default = False, description = "Debug mode flag")

    database_url: str = Field(
        default =
        "postgresql://postgres:devpassword@localhost:5432/multimodal_search_dev",
        description = "PostgreSQL connection URL with pgvector support",
    )
    db_pool_min_size: int = Field(
        default = 10,
        ge = 1,
        description = "Min DB connections"
    )
    db_pool_max_size: int = Field(
        default = 20,
        ge = 1,
        description = "Max DB connections"
    )
    db_pool_timeout: float = Field(
        default = 30.0,
        gt = 0,
        description = "Connection timeout in seconds"
    )
    db_command_timeout: float = Field(
        default = 60.0,
        gt = 0,
        description = "Query timeout in seconds"
    )

    redis_url: str = Field(
        default = "redis://localhost:6379/0",
        description = "Redis connection URL for caching",
    )
    redis_decode_responses: bool = Field(
        default = True,
        description = "Decode Redis responses to strings"
    )
    redis_pool_max_size: int = Field(
        default = 50,
        ge = 1,
        description = "Max Redis connections in pool"
    )

    rate_limit_upload: str = Field(
        default = "100/minute",
        description = "Rate limit for upload endpoints"
    )
    rate_limit_search: str = Field(
        default = "60/minute",
        description = "Rate limit for search endpoints"
    )
    rate_limit_auth: str = Field(
        default = "50/minute",
        description = "Rate limit for auth endpoints"
    )
    rate_limit_common: str = Field(
        default = "100/minute",
        description = "Rate limit for common/public endpoints"
    )

    secret_key: str = Field(
        default = "dev-secret-key",
        description = "Secret key for JWT signing (dev)"
    )
    algorithm: str = Field(
        default = "HS256",
        description = "JWT signing algorithm"
    )

    ollama_host: str = Field(
        default = "http://ollama:11434",
        description = "Ollama API host"
    )
    vision_model: str = Field(
        default = "qwen2.5vl:3b",
        description = "Ollama vision model for image/video analysis"
    )
    local_embedding_model: str = Field(
        default = "bge-m3",
        description = "Local embedding model (bge-m3)"
    )
    local_embedding_dimensions: int = Field(
        default = 1024,
        gt = 0,
        description = "Local embedding vector dimensions"
    )
    max_concurrent_vision: int = Field(
        default = 1,
        ge = 1,
        description = "Max concurrent vision inferences"
    )
    max_concurrent_embedding: int = Field(
        default = 2,
        ge = 1,
        description = "Max concurrent embedding operations"
    )

    upload_path: Path = Field(
        default = Path("./storage/uploads"),
        description = "Base path for uploaded files"
    )
    max_upload_size: int = Field(
        default = 104_857_600,  # 100MB
        gt = 0,
        description = "Maximum upload file size in bytes",
    )

    cors_origins: list[str] = Field(
        default = [
            "http://localhost:3000",
            "http://192.168.1.167:3000",
            "http://localhost:5173",
            "http://localhost:856",
            "http://192.168.1.167:856",
            "http://localhost"
        ],
        description = "Allowed CORS origins",
    )

    default_page_size: int = Field(
        default = 50,
        ge = 1,
        le = 100,
        description = "Default pagination size"
    )
    max_page_size: int = Field(
        default = 100,
        ge = 1,
        description = "Maximum pagination size"
    )

    video_frame_sample_rate: int = Field(
        default = 1,
        ge = 1,
        description = "Sample every Nth frame for video analysis"
    )
    max_video_frames: int = Field(
        default = 10,
        ge = 1,
        description = "Maximum frames to extract from video"
    )
    thumbnail_size: tuple[
        int,
        int] = Field(
            default = (256,
                       256),
            description = "Thumbnail dimensions (width, height)"
        )
    vision_max_image_size: int = Field(
        default = 1568,
        ge = 224,
        description = "Max image dimension for vision model (pixels)"
    )
    vision_patch_size: int = Field(
        default = 28,
        ge = 1,
        description = "Vision model patch size for dimension alignment"
    )
    vision_jpeg_quality: int = Field(
        default = 88,
        ge = 1,
        le = 100,
        description = "JPEG quality for vision preprocessing"
    )

    @field_validator("cors_origins", mode = "before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Parse CORS origins from comma-separated string or list
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate environment is one of allowed values
        """
        allowed = {"development", "staging", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """
        Warn if using default secret key in production
        """
        if info.data.get("environment"
                         ) == "production" and v == "dev-secret-key":
            # just warn for now
            warnings.warn(
                "Using default secret key in production is insecure!",
                stacklevel = 2
            )
        return v

    @property
    def allowed_mime_types(self) -> set[str]:
        """
        Get all allowed MIME types for upload
        Imported from file validator
        """
        # Prevent circular import
        from core.validators.file import ALLOWED_MIME_TYPES
        return ALLOWED_MIME_TYPES

    @property
    def allowed_image_types(self) -> set[str]:
        """
        Get allowed image MIME types.
        Imported from file validator (single source of truth)
        """
        # Prevent circular import
        from core.validators.file import ALLOWED_IMAGE_MIMES
        return ALLOWED_IMAGE_MIMES

    @property
    def allowed_video_types(self) -> set[str]:
        """
        Get allowed video MIME types.
        Imported from file validator (single source of truth)
        """
        # Prevent circular import
        from core.validators.file import ALLOWED_VIDEO_MIMES
        return ALLOWED_VIDEO_MIMES

    @property
    def is_production(self) -> bool:
        """
        Check if running in production environment
        """
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """
        Check if running in development environment
        """
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()


settings = get_settings()
