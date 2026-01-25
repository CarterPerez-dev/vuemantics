"""
Authentication package for JWT tokens and dependencies.
"""

from .jwt_auth import (
    create_token_pair,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_current_active_user,
    refresh_access_token,
    TokenType,
)
from .dependencies import verify_upload_ownership

__all__ = [
    # JWT functions
    "create_token_pair",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "get_current_active_user",
    "refresh_access_token",
    "TokenType",
    # Dependencies
    "verify_upload_ownership",
]
