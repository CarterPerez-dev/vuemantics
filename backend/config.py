"""
Application configuration using Pydantic Settings.
---
Loads configuration from environment variables with validation and type conversion.
Follows 12-factor app principles for configuration management.
---
/backend/config.py
"""

import warnings
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # Application
    app_name: str = Field(default="PG-VENV", description="Application name")
    environment: str = Field(
        default="development",
        description="Runtime environment (development/staging/production)",
    )
    debug: bool = Field(default=False, description="Debug mode flag")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:devpassword@localhost:5432/multimodal_search_dev",
        description="PostgreSQL connection URL with pgvector support",
    )
    db_pool_min_size: int = Field(default=10, ge=1, description="Min DB connections")
    db_pool_max_size: int = Field(default=20, ge=1, description="Max DB connections")
    db_pool_timeout: float = Field(
        default=30.0, gt=0, description="Connection timeout in seconds"
    )
    db_command_timeout: float = Field(
        default=60.0, gt=0, description="Query timeout in seconds"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching",
    )
    redis_decode_responses: bool = Field(
        default=True, description="Decode Redis responses to strings"
    )

    # JWT Authentication
    secret_key: str = Field(
        default="dev-secret-key", description="Secret key for JWT signing (dev)"
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")

    # AI Services
    openai_api_key: str = Field(default="", description="OpenAI API key for embeddings")
    gemini_api_key: str = Field(
        default="", description="Google Gemini API key for media analysis"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model to use"
    )
    embedding_dimensions: int = Field(
        default=1536, gt=0, description="Embedding vector dimensions"
    )

    # Storage
    upload_path: Path = Field(
        default=Path("./storage/uploads"), description="Base path for uploaded files"
    )
    max_upload_size: int = Field(
        default=104_857_600,  # 100MB
        gt=0,
        description="Maximum upload file size in bytes",
    )
    allowed_image_types: set[str] = Field(
        default={
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp",
            "image/heic",
            "image/heif",
        },
        description="Allowed MIME types for images",
    )
    allowed_video_types: set[str] = Field(
        default={
            "video/mp4",
            "video/mpeg",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-flv",
            "video/webm",
        },
        description="Allowed MIME types for videos",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost"],
        description="Allowed CORS origins",
    )

    # Pagination
    default_page_size: int = Field(
        default=20, ge=1, le=100, description="Default pagination size"
    )
    max_page_size: int = Field(default=100, ge=1, description="Maximum pagination size")

    # Processing
    video_frame_sample_rate: int = Field(
        default=1, ge=1, description="Sample every Nth frame for video analysis"
    )
    max_video_frames: int = Field(
        default=10, ge=1, description="Maximum frames to extract from video"
    )
    thumbnail_size: tuple[int, int] = Field(
        default=(256, 256), description="Thumbnail dimensions (width, height)"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate environment is one of allowed values.
        """
        allowed = {"development", "staging", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("upload_path")
    @classmethod
    def ensure_upload_path_exists(cls, v: Path) -> Path:
        """
        Ensure upload directory exists, create if not.
        """
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """
        Warn if using default secret key in production.
        """
        if info.data.get("environment") == "production" and v == "dev-secret-key":
            # For MVP, just warn
            warnings.warn(
                "Using default secret key in production is insecure!", stacklevel=2
            )
        return v

    @field_validator("openai_api_key", "gemini_api_key")
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        """
        Validate API keys are present.
        """
        env = info.data.get("environment")
        if not v and env not in ("development", "testing"):
            field_name = info.field_name
            raise ValueError(f"{field_name} is required in {env} environment")
        return v

    @property
    def allowed_mime_types(self) -> set[str]:
        """
        Get all allowed MIME types for upload.
        """
        return self.allowed_image_types.union(self.allowed_video_types)

    @property
    def is_production(self) -> bool:
        """
        Check if running in production environment.
        """
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """
        Check if running in development environment.
        """
        return self.environment == "development"

    def get_db_url_with_driver(self) -> str:
        """
        Get database URL with asyncpg driver.
        """
        # Replace postgresql:// with postgresql+asyncpg:// if needed
        if self.database_url.startswith("postgresql://"):
            return self.database_url
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()
