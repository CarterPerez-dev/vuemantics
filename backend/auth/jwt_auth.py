"""
JWT authentication with access and refresh tokens.

Implements dual-token authentication:
- Access tokens: 30 minutes, used for API requests
- Refresh tokens: 30 days, used to get new access tokens
---
/backend/auth/jwt_auth.py
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Final
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from config import settings
from models import User

# Token configuration
ALGORITHM: Final[str] = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 30  # 30 days

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class TokenType:
    """
    Token type constants.
    """

    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(user_id: UUID) -> str:
    """
    Create a JWT access token for API requests.
    (expires in 30 minutes)
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": TokenType.ACCESS,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """
    Create a JWT refresh token for getting new access tokens.
    (expires in 30 days)
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": TokenType.REFRESH,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_token_pair(user_id: UUID) -> dict[str, str]:
    """
    Create both access and refresh tokens.
    """
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])

        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}",
            )

        return payload

    except JWTError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    FastAPI dependency to get current authenticated user.
    """
    payload = decode_token(token, expected_type=TokenType.ACCESS)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user = await User.find_by_id(UUID(user_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        ) from e

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency for active users only.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return current_user


async def refresh_access_token(refresh_token: str) -> dict[str, str]:
    """
    Use refresh token to get new access token.
    """
    payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = await User.find_by_id(UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token only
    # Refresh token stays valid for its full 30 days
    return {
        "access_token": create_access_token(UUID(user_id)),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# Optional: Dependency for optional authentication (so like public endpoints)
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
    except HTTPException:
        return None
