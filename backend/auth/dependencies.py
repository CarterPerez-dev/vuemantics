"""
ⒸAngelaMos | 2026
dependencies.py
"""

import asyncio
import contextlib
import logging
from uuid import UUID

from fastapi import Depends, WebSocket
from starlette.websockets import WebSocketDisconnect

from auth import get_current_user
from auth.jwt_auth import decode_token, TokenType
from core import NotFoundError, AuthenticationError
from core.websocket.messages import AuthSuccess, AuthError
from models.Upload import Upload
from models.User import User
import config


logger = logging.getLogger(__name__)


async def verify_upload_ownership(
    upload_id: UUID,
    current_user: User = Depends(get_current_user),
) -> Upload:
    """
    Verify user owns the upload and return it
    """
    upload = await Upload.find_by_id(upload_id)

    if not upload or upload.user_id != current_user.id:
        raise NotFoundError("Upload not found")

    return upload


async def authenticate_websocket(websocket: WebSocket) -> str | None:
    """
    Authenticate WebSocket connection via first message pattern

    Returns:
        User ID if authentication successful, None otherwise
    """
    origin = websocket.headers.get("origin", "")
    if origin and origin not in config.settings.cors_origins:
        logger.warning(f"WebSocket from unauthorized origin: {origin}")
        return None

    await websocket.accept()

    try:
        auth_data = await asyncio.wait_for(
            websocket.receive_json(),
            timeout = config.WEBSOCKET_AUTH_TIMEOUT
        )
    except TimeoutError:
        await websocket.send_json(
            AuthError(message = "Authentication timeout").model_dump()
        )
        await websocket.close(
            code = config.WEBSOCKET_CLOSE_AUTH_TIMEOUT,
            reason = "Authentication timeout"
        )
        return None
    except WebSocketDisconnect:
        logger.debug(
            "WebSocket disconnected before auth (likely React StrictMode)"
        )
        return None
    except Exception as e:
        logger.error(f"Error receiving auth message: {e}")
        with contextlib.suppress(RuntimeError):
            await websocket.close(
                code = config.WEBSOCKET_CLOSE_INVALID_MESSAGE,
                reason = "Invalid message format"
            )
        return None

    if auth_data.get("type") != "auth" or not auth_data.get("token"):
        await websocket.send_json(
            AuthError(message = "Authentication required").model_dump()
        )
        await websocket.close(
            code = config.WEBSOCKET_CLOSE_AUTH_REQUIRED,
            reason = "Authentication required"
        )
        return None

    try:
        payload = decode_token(
            auth_data["token"],
            expected_type = TokenType.ACCESS
        )

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Missing user ID in token")

        user = await User.find_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        token_version = payload.get("token_version", 0)
        if token_version != user.token_version:
            raise AuthenticationError("Token has been invalidated")

        await websocket.send_json(
            AuthSuccess(user_id = user_id).model_dump()
        )

        return user_id

    except AuthenticationError as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.send_json(AuthError(message = str(e)).model_dump())
        await websocket.close(
            code = config.WEBSOCKET_CLOSE_INVALID_TOKEN,
            reason = "Invalid token"
        )
        return None
