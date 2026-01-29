"""
ⒸAngelaMos | 2026
publisher.py
"""

import asyncio
import logging

from fastapi import WebSocket

from core.redis import redis_pool
from core.websocket.manager import get_manager
from core.websocket.messages import ServerMessage


logger = logging.getLogger(__name__)


class UploadProgressPublisher:
    """
    Publishes upload progress events via Redis pub/sub

    Handles cross instance message delivery and local distribution
    Listens to Redis channels and forwards to connected WebSocket clients
    """
    def __init__(self) -> None:
        """
        Initialize publisher
        """
        self._listener_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """
        Start Redis listener background task
        """
        if self._running:
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_redis())
        logger.info("UploadProgressPublisher started")

    async def stop(self) -> None:
        """
        Stop Redis listener
        """
        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await asyncio.wait_for(self._listener_task, timeout = 2.0)
            except asyncio.CancelledError:
                pass
            except TimeoutError:
                logger.warning(
                    "Redis listener task did not stop within timeout, forcing shutdown"
                )
            except Exception as e:
                logger.error(f"Error stopping Redis listener: {e}")

        logger.info("UploadProgressPublisher stopped")

    async def publish_progress(
        self,
        upload_id: str,
        message: ServerMessage
    ) -> None:
        """
        Publish upload progress to Redis

        Args:
            upload_id: Upload's ID
            message: Progress message to broadcast
        """
        channel = f"upload:{upload_id}"
        payload = message.model_dump_json()

        try:
            await redis_pool.publish(channel, payload)
            logger.debug(f"Published progress for upload {upload_id}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")

    async def publish_to_user(
        self,
        user_id: str,
        message: ServerMessage
    ) -> None:
        """
        Publish message directly to a user

        Args:
            user_id: User's ID
            message: Message to broadcast
        """
        channel = f"user:{user_id}"
        payload = message.model_dump_json()

        try:
            await redis_pool.publish(channel, payload)
            logger.debug(f"Published message to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")

    async def _listen_redis(self) -> None:
        """
        Background task that listens to Redis pub/sub

        Receives messages from Redis and
        forwards to local WebSocket connections
        """
        pubsub = None
        try:
            pubsub = await redis_pool.psubscribe("upload:*", "user:*")

            logger.info("Redis listener started (patterns: upload:*, user:*)")

            while self._running:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages = True,
                        timeout = 0.1
                    )

                    if message is None:
                        continue

                    if message["type"] != "pmessage":
                        continue

                    # Note: decode_responses=True means these are already strings
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode("utf-8")

                    payload = message["data"]
                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8")

                    manager = get_manager()

                    user_ids: list[str]
                    if channel.startswith("upload:"):
                        upload_id = channel.split(":", 1)[1]
                        user_ids = list(manager.get_upload_subscriber_ids(upload_id))
                    elif channel.startswith("user:"):
                        user_id = channel.split(":", 1)[1]
                        user_ids = [user_id]
                    else:
                        continue

                    for user_id in user_ids:
                        connections = list(
                            manager.user_connections.get(user_id,
                                                         set())
                        )
                        dead_connections: set[WebSocket] = set()

                        for ws in connections:
                            try:
                                await ws.send_text(payload)
                            except Exception as e:
                                logger.debug(
                                    f"Failed to forward message to user {user_id}: {e}"
                                )
                                dead_connections.add(ws)

                        # Garbage c
                        for ws in dead_connections:
                            await manager.disconnect(user_id, ws)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in Redis listener: {e}")
                    if self._running:
                        await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            if pubsub:
                try:
                    await asyncio.wait_for(
                        pubsub.unsubscribe(),
                        timeout = 0.5
                    )
                    await asyncio.wait_for(pubsub.close(), timeout = 0.5)
                except TimeoutError:
                    logger.warning(
                        "Timeout closing pubsub connection (non-critical)"
                    )
                except Exception as e:
                    logger.error(f"Error closing pubsub: {e}")


# DI
_publisher: UploadProgressPublisher | None = None


def init_publisher() -> None:
    """
    Initialize global publisher
    """
    global _publisher
    _publisher = UploadProgressPublisher()
    logger.info("UploadProgressPublisher initialized")


def get_publisher() -> UploadProgressPublisher:
    """
    Get publisher instance
    """
    if _publisher is None:
        raise RuntimeError(
            "UploadProgressPublisher not initialized. Call init_publisher()"
        )
    return _publisher
