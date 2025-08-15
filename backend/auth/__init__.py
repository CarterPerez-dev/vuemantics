"""
Authentication package for JWT and password management.
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
from .password import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_secure_token,
)

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
    # Password functions
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "generate_secure_token",
]
