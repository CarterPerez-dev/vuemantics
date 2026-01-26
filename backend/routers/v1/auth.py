"""
ⒸAngelaMos | 2026
Authentication routes for user registration, login, and token management.

Implements OAuth2-compatible endpoints with JWT access/refresh tokens.
Follows FastAPI patterns with dependency injection and Pydantic validation.
Includes rate limiting to prevent brute force attacks.
"""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from auth import (
    create_token_pair,
    get_current_user,
    refresh_access_token,
)
from config import settings
from core import (
    AUTH_401,
    CONFLICT_409,
    FORBIDDEN_403,
    RATE_LIMIT_420,
    VALIDATION_422,
    AuthenticationError,
    ConflictError,
    ValidationError,
    hash_password,
    limiter,
    verify_password_safe,
)
from models.User import User
from schemas import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/auth",
    tags = ["authentication"],
    responses = {
        **AUTH_401,
        **FORBIDDEN_403,
        **CONFLICT_409,
        **VALIDATION_422,
        **RATE_LIMIT_420,
    },
)


@router.post(
    "/register",
    response_model = UserResponse,
    status_code = status.HTTP_201_CREATED,
    summary = "Register new user",
    description = "Create a new user account with email and password",
)
@limiter.limit(settings.rate_limit_auth)
async def register(
    request: Request,
    user_data: UserCreate
) -> UserResponse:
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
        raise ConflictError("Email already registered")

    try:
        password_hash = await hash_password(user_data.password)
        user = await User.create(
            email = user_data.email,
            password_hash = password_hash,
            is_active = True
        )

        logger.info(f"New user registered: {user.email}")
        return UserResponse.model_validate(user)

    except ValueError as e:
        raise ValidationError(str(e)) from e
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise


@router.post(
    "/token",
    response_model = TokenResponse,
    summary = "Login with email and password",
    description =
    "OAuth2 compatible token endpoint. Returns access and refresh tokens.",
)
@limiter.limit(settings.rate_limit_auth)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm,
                         Depends()]
) -> TokenResponse:
    """
    OAuth2 compatible token endpoint.
    Returns both access token (30 min) and refresh token (30 days).
    """
    user = await User.find_active_by_email(form_data.username)

    password_hash = user.password_hash if user else None
    is_valid = await verify_password_safe(
        form_data.password,
        password_hash
    )

    if not is_valid or not user:
        raise AuthenticationError("Incorrect email or password")

    if user.id is None:
        raise AuthenticationError("Invalid user state")
    tokens = create_token_pair(user.id, user.token_version)

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(**tokens)


@router.post(
    "/token/refresh",
    response_model = TokenResponse,
    summary = "Refresh access token",
    description = "Use refresh token to get new access token",
)
@limiter.limit(settings.rate_limit_common)
async def refresh_token(
    request: Request,
    refresh_data: RefreshRequest
) -> TokenResponse:
    """
    Refresh access token using valid refresh token.
    Returns new access token and same refresh token. (30d)
    """
    try:
        tokens = await refresh_access_token(refresh_data.refresh_token)
        return TokenResponse(**tokens)
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise


@router.get(
    "/me",
    response_model = UserResponse,
    summary = "Get current user",
    description = "Get authenticated user's information",
)
@limiter.limit(settings.rate_limit_common)
async def get_me(
    request: Request,
    current_user: Annotated[User,
                            Depends(get_current_user)]
) -> UserResponse:
    """
    Get current authenticated user information.
    """
    return UserResponse.model_validate(current_user)
