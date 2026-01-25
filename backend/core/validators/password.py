"""
ⒸAngelaMos | 2026
password.py
Password hashing and validation utilities
"""

import re
import asyncio
import secrets

import bcrypt

import config


DUMMY_HASH = bcrypt.hashpw(
    b"dummy_password_for_timing_attack_prevention",
    bcrypt.gensalt(rounds = config.BCRYPT_ROUNDS)
).decode('utf-8')


async def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Runs in thread pool to avoid blocking the async event loop
    since bcrypt is CPU intensive by design.
    """
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_msg)

    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds = config.BCRYPT_ROUNDS)

    def _hash() -> str:
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    return await asyncio.to_thread(_hash)


async def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verify a password against its hash
    Runs in thread pool to avoid blocking the async event loop
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')

        def _verify() -> bool:
            return bcrypt.checkpw(password_bytes, hashed_bytes)

        return await asyncio.to_thread(_verify)
    except Exception:
        return False


async def verify_password_safe(
    plain_password: str,
    hashed_password: str | None,
) -> bool:
    """
    Verify password with constant time behavior

    Prevents user enumeration via timing attacks by always
    performing a hash operation even when user doesn't exist
    """
    if hashed_password is None:
        await verify_password(plain_password, DUMMY_HASH)
        return False

    return await verify_password(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    """
    return secrets.token_urlsafe(length)


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """
    Validate password meets minimum security requirements

    Password must have:
    - At least 8 characters
    - At most 72 characters (bcrypt max)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if not password:
        return False, "Password is required"

    if len(password) < config.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters long"

    if len(password) > config.MAX_PASSWORD_LENGTH:
        return (
            False,
            f"Password must be no more than {config.MAX_PASSWORD_LENGTH} characters long",
        )

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    if not re.search(rf"[{re.escape(config.SPECIAL_CHARACTERS)}]",
                     password):
        return (
            False,
            f"Password must contain at least one special character ({config.SPECIAL_CHARACTERS})",
        )

    return True, None
