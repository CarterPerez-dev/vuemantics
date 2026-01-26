"""
ⒸAngelaMos | 2026
user.py
"""

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)

from config import (
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
)
from core import validate_password_strength
from schemas import TimestampMixin


class UserBase(BaseModel):
    """
    Base user fields.
    """
    email: EmailStr = Field(
        description = "User's email address",
    )


class UserCreate(UserBase):
    """
    User registration request with password validation
    """
    model_config = ConfigDict(
        extra = "forbid",
        str_strip_whitespace = True,
    )

    password: str = Field(
        description =
        f"Password ({MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} chars, must include uppercase, lowercase, number, special char)",
        min_length = MIN_PASSWORD_LENGTH,
        max_length = MAX_PASSWORD_LENGTH,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password using centralized validation logic.
        """
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UserResponse(UserBase, TimestampMixin):
    """
    User response with all public fields.
    """

    model_config = ConfigDict(
        extra = "forbid",
        from_attributes = True,
    )

    id: UUID = Field(description = "User's unique identifier")
    is_active: bool = Field(description = "Whether account is active")


class UserUpdate(BaseModel):
    """
    User profile update request
    """
    model_config = ConfigDict(
        extra = "forbid",
        str_strip_whitespace = True,
    )

    email: EmailStr | None = Field(
        default = None,
        description = "New email address"
    )
    current_password: str | None = Field(
        default = None,
        description = "Current password (required for email change)"
    )


class PasswordChangeRequest(BaseModel):
    """
    Password change request
    """
    model_config = ConfigDict(
        extra = "forbid",
        str_strip_whitespace = True,
    )

    current_password: str = Field(
        description = "Current password",
        min_length = 1
    )
    new_password: str = Field(
        description = "New password",
        min_length = MIN_PASSWORD_LENGTH,
        max_length = MAX_PASSWORD_LENGTH
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str, info: ValidationInfo) -> str:
        """
        Validate new password using centralized validation logic.
        """
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)

        if "current_password" in info.data and v == info.data[
                "current_password"]:
            raise ValueError(
                "New password must be different from current password"
            )

        return v


class UserStats(BaseModel):
    """
    User statistics response
    """
    model_config = ConfigDict(
        extra = "forbid",
    )

    total_uploads: int = Field(
        ge = 0,
        description = "Total number of uploads"
    )
    uploads_by_status: dict[
        str,
        int] = Field(description = "Upload counts by processing status")
    storage_used_bytes: int = Field(
        ge = 0,
        description = "Total storage used in bytes"
    )
    last_upload_at: datetime | None = Field(
        description = "Timestamp of last upload"
    )
