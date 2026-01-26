"""
ⒸAngelaMos | 2026
websocket.py
"""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from auth.dependencies import authenticate_websocket
from core.websocket import get_manager
from core.websocket.messages import (
    Heartbeat,
    SubscribeUpload,
    UnsubscribeUpload,
)
import config


logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/uploads")
async def upload_progress_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time upload progress updates

    Flow:
        1. Client connects
        2. Server waits for auth message (5s timeout)
        3. Client sends {"type": "auth", "token": "..."}
        4. Server validates JWT and sends auth_success
        5. Client subscribes to specific uploads
        6. Server streams progress updates in real-time

    Close codes:
        4001: Authentication timeout
        4002: Authentication required
        4003: Invalid token
        1000: Normal closure
    """
    user_id = await authenticate_websocket(websocket)
    if not user_id:
        return

    manager = get_manager()
    await manager.connect(user_id, websocket)

    async def send_heartbeat():
        """
        Send periodic heartbeat to keep connection alive
        """
        try:
            while True:
                await asyncio.sleep(config.WEBSOCKET_HEARTBEAT_INTERVAL)
                if websocket.client_state.value == 1:
                    await websocket.send_json(Heartbeat().model_dump())
        except Exception as e:
            logger.debug(f"Heartbeat task stopped: {e}")

    async def receive_messages():
        """
        Handle incoming client messages
        """
        try:
            async for raw_message in websocket.iter_json():
                try:
                    action = raw_message.get("action")

                    if action == "subscribe_upload":
                        msg = SubscribeUpload.model_validate(raw_message)
                        await manager.subscribe_upload(user_id, msg.upload_id)
                        logger.info(
                            f"User {user_id} subscribed to upload {msg.upload_id}"
                        )

                    elif action == "unsubscribe_upload":
                        msg = UnsubscribeUpload.model_validate(raw_message)
                        await manager.unsubscribe_upload(user_id, msg.upload_id)
                        logger.info(
                            f"User {user_id} unsubscribed from upload {msg.upload_id}"
                        )

                    elif action == "pong":
                        pass

                    elif action == "ping":
                        # Client sent ping, respond with pong
                        pass

                    else:
                        logger.warning(
                            f"Unknown action from user {user_id}: {action}"
                        )

                except ValidationError as e:
                    logger.error(f"Invalid message format: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected (WebSocketDisconnect)")

    try:
        await asyncio.gather(
            send_heartbeat(),
            receive_messages(),
        )
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await manager.disconnect(user_id, websocket)
