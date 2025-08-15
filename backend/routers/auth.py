"""
Authentication routes for user registration, login, and token management.

Implements OAuth2-compatible endpoints with JWT access/refresh tokens.
Follows FastAPI patterns with dependency injection and Pydantic validation.
Includes rate limiting to prevent brute force attacks.
---
/backend/routers/auth.py
"""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import (
    create_token_pair,
    get_current_user,
    hash_password,
    refresh_access_token,
    verify_password,
)
from models import User
from schemas import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

logger = logging.getLogger(__name__)

# TODO: Lower limits when prod
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        429: {"description": "Too Many Requests"},
    },
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password",
)
@limiter.limit("50/minute")
async def register(request: Request, user_data: UserCreate) -> UserResponse:
    """
    Register a new user.

    Password requirements:
    - 8-69 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """
    existing_user = await User.find_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    try:
        password_hash = hash_password(user_data.password)
        user = await User.create(
            email=user_data.email, password_hash=password_hash, is_active=True
        )

        logger.info(f"New user registered: {user.email}")
        return UserResponse.model_validate(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        ) from e


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="OAuth2 compatible token endpoint. Returns access and refresh tokens.",
)
@limiter.limit("50/minute")
async def login(
    request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenResponse:
    """
    OAuth2 compatible token endpoint.
    Returns both access token (30 min) and refresh token (30 days).
    """
    user = await User.find_active_by_email(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = create_token_pair(user.id)

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(**tokens)


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use refresh token to get new access token",
)
@limiter.limit("100/minute")
async def refresh_token(
    request: Request, refresh_data: RefreshRequest
) -> TokenResponse:
    """
    Refresh access token using valid refresh token.
    Returns new access token and same refresh token. (30d)
    """
    try:
        tokens = await refresh_access_token(refresh_data.refresh_token)
        return TokenResponse(**tokens)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        ) from e


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get authenticated user's information",
)
@limiter.limit("100/minute")
async def get_me(
    request: Request, current_user: Annotated[User, Depends(get_current_user)]
) -> UserResponse:
    """
    Get current authenticated user information.
    """
    return UserResponse.model_validate(current_user)
