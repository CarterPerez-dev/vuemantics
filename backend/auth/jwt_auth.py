"""
ⒸAngelaMos | 2026
jwt_auth.py
"""

from typing import Any
from uuid import UUID
from datetime import datetime, timedelta, UTC

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

import config
from core import (
    AuthenticationError,
    AuthorizationError,
    BaseAppException,
)
from models.User import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/auth/token")


class TokenType:
    """
    Token type constants.
    """
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(user_id: UUID, token_version: int = 0) -> str:
    """
    Create a JWT access token for API requests
    """
    expire = datetime.now(UTC) + timedelta(
        minutes = config.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": TokenType.ACCESS,
        "token_version": token_version,
    }

    return jwt.encode(
        payload,
        config.settings.secret_key,
        algorithm = config.settings.algorithm
    )


def create_refresh_token(user_id: UUID) -> str:
    """
    Create a JWT refresh token for getting new access tokens
    """
    expire = datetime.now(UTC) + timedelta(
        days = config.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": TokenType.REFRESH,
    }

    encoded: str = jwt.encode(
        payload,
        config.settings.secret_key,
        algorithm = config.settings.algorithm
    )
    return encoded


def create_token_pair(user_id: UUID,
                      token_version: int = 0) -> dict[str,
                                                      str]:
    """
    Create both access and refresh tokens
    """
    return {
        "access_token": create_access_token(user_id,
                                            token_version),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


def decode_token(token: str,
                 expected_type: str | None = None) -> dict[str,
                                                           Any]:
    """
    Decode and validate a JWT token
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            config.settings.secret_key,
            algorithms = [config.settings.algorithm]
        )

        if expected_type and payload.get("type") != expected_type:
            raise AuthenticationError(
                f"Invalid token type. Expected {expected_type}"
            )

        return payload

    except JWTError as e:
        if "expired" in str(e).lower():
            raise AuthenticationError("Token has expired") from e
        raise AuthenticationError("Could not validate token") from e


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    FastAPI dependency to get current authenticated user
    """
    payload = decode_token(token, expected_type = TokenType.ACCESS)

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")

    token_version = payload.get("token_version", 0)

    try:
        user = await User.find_by_id(UUID(user_id))
    except ValueError as e:
        raise AuthenticationError("Invalid user ID format") from e

    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthorizationError("User account is deactivated")

    if token_version != user.token_version:
        raise AuthenticationError("Token has been invalidated")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency for active users only
    """
    if not current_user.is_active:
        raise AuthorizationError("User account is deactivated")
    return current_user


async def refresh_access_token(refresh_token: str) -> dict[str, str]:
    """
    Use refresh token to get new access token
    """
    payload = decode_token(
        refresh_token,
        expected_type = TokenType.REFRESH
    )

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid refresh token")

    user = await User.find_by_id(UUID(user_id))
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return {
        "access_token":
        create_access_token(UUID(user_id),
                            user.token_version),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# If: Dependency for optional authentication (public endpoints)
async def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme),
) -> User | None:
    """
    FastAPI dependency for optional authentication.
    """
    if token is None:
        return None

    try:
        return await get_current_user(token)
    except BaseAppException:
        return None
