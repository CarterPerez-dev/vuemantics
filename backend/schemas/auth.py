"""
ⒸAngelaMos | 2026
auth.py
"""

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from config import MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH


class LoginRequest(BaseModel):
    """
    Login request with email and password
    """
    model_config = ConfigDict(
        extra = "ignore",  # Allow extra fields for MVP
        str_strip_whitespace = True,
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "MyStr0ng!Pass123"}
        },
    )

    email: EmailStr = Field(
        description = "User's email address",
        examples = ["user@example.com"]
    )
    password: str = Field(
        description = "User's password",
        min_length = 1,
        examples = ["MyStr0ng!Pass123"]
    )


class TokenResponse(BaseModel):
    """
    JWT token pair response
    """
    model_config = ConfigDict(
        extra = "ignore",
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
            }
        },
    )

    access_token: str = Field(
        description = "JWT access token (30 min expiry)"
    )
    refresh_token: str = Field(
        description = "JWT refresh token (30 day expiry)"
    )
    token_type: str = Field(
        default = "bearer",
        description = "Token type (always 'bearer')"
    )


class RefreshRequest(BaseModel):
    """
    Refresh token request
    """
    model_config = ConfigDict(
        extra = "ignore",
        str_strip_whitespace = True,
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        },
    )

    refresh_token: str = Field(
        description = "Valid refresh token",
        min_length = 1
    )


class PasswordResetRequest(BaseModel):
    """
    Password reset request (future feature)
    """
    model_config = ConfigDict(
        extra = "ignore",
        str_strip_whitespace = True,
    )

    email: EmailStr = Field(description = "Email to send reset link")


class PasswordResetConfirm(BaseModel):
    """
    Confirm password reset with new password (future feature).
    """
    model_config = ConfigDict(
        extra = "ignore",
        str_strip_whitespace = True,
    )

    token: str = Field(description = "Password reset token")
    new_password: str = Field(
        description = "New password",
        min_length = MIN_PASSWORD_LENGTH,
        max_length = MAX_PASSWORD_LENGTH
    )
