"""
Password hashing and validation utilities.

Uses bcrypt with 14 rounds for secure password hashing.
Includes validation for strong passwords with multiple character types.
---
/backend/auth/password.py
"""

import re
import secrets

from settings import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    SPECIAL_CHARACTERS,
    pwd_context,
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with 14 rounds.
    """
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_msg)

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    """
    return secrets.token_urlsafe(length)


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """
    Validate password meets minimum security requirements.

    Password must have:
    - At least 8 characters
    - At most 69 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """
    if not password:
        return False, "Password is required"

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

    if len(password) > MAX_PASSWORD_LENGTH:
        return (
            False,
            f"Password must be no more than {MAX_PASSWORD_LENGTH} characters long",
        )

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    # Check for at least one number
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    # Check for at least one special character
    if not re.search(rf"[{re.escape(SPECIAL_CHARACTERS)}]", password):
        return (
            False,
            f"Password must contain at least one special character ({SPECIAL_CHARACTERS})",
        )

    return True, None
