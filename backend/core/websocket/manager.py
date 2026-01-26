"""
ⒸAngelaMos | 2026
manager.py
"""

import logging
from collections import defaultdict

from fastapi import WebSocket

from core.websocket.messages import ServerMessage


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and subscriptions

    Handles connection lifecycle and routing messages to subscribers
    Does NOT handle Redis pub/sub (that's in publisher.py)
    """
    def __init__(self) -> None:
        """
        Initialize connection manager
        """
        self.user_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self.upload_subscribers: dict[str, set[str]] = defaultdict(set)
        self.user_subscriptions: dict[str, set[str]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Register new WebSocket connection

        Args:
            user_id: User's ID
            websocket: WebSocket connection
        """
        self.user_connections[user_id].add(websocket)
        logger.info(
            f"User {user_id} connected "
            f"(total connections: {len(self.user_connections[user_id])})"
        )

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Unregister WebSocket connection and clean up subscriptions

        Args:
            user_id: User's ID
            websocket: WebSocket connection
        """
        self.user_connections[user_id].discard(websocket)

        if not self.user_connections[user_id]:
            del self.user_connections[user_id]

            # Clean up all subscriptions for this user
            for upload_id in list(self.user_subscriptions.get(user_id,
                                                              [])):
                await self.unsubscribe_upload(user_id, upload_id)

        logger.info(f"User {user_id} disconnected")

    async def subscribe_upload(self, user_id: str, upload_id: str) -> None:
        """
        Subscribe user to upload progress updates

        Args:
            user_id: User's ID
            upload_id: Upload's ID
        """
        self.upload_subscribers[upload_id].add(user_id)
        self.user_subscriptions[user_id].add(upload_id)
        logger.debug(f"User {user_id} subscribed to upload {upload_id}")

    async def unsubscribe_upload(
        self,
        user_id: str,
        upload_id: str
    ) -> None:
        """
        Unsubscribe user from upload updates

        Args:
            user_id: User's ID
            upload_id: Upload's ID
        """
        self.upload_subscribers[upload_id].discard(user_id)
        self.user_subscriptions[user_id].discard(upload_id)

        if not self.upload_subscribers[upload_id]:
            del self.upload_subscribers[upload_id]
        if not self.user_subscriptions[user_id]:
            del self.user_subscriptions[user_id]

    async def send_to_user(
        self,
        user_id: str,
        message: ServerMessage
    ) -> None:
        """
        Send message to all connections for a specific user

        Args:
            user_id: User's ID
            message: Message to send
        """
        connections = self.user_connections.get(user_id, set())
        dead_connections: set[WebSocket] = set()

        for ws in connections:
            try:
                await ws.send_json(message.model_dump(mode = "json"))
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            await self.disconnect(user_id, ws)

    async def send_to_upload_subscribers(
        self,
        upload_id: str,
        message: ServerMessage
    ) -> None:
        """
        Send message to all users subscribed to an upload

        Args:
            upload_id: Upload's ID
            message: Message to send
        """
        user_ids = self.upload_subscribers.get(upload_id, set())

        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    def get_upload_subscriber_ids(self, upload_id: str) -> set[str]:
        """
        Get all user IDs subscribed to an upload
        """
        return self.upload_subscribers.get(upload_id, set()).copy()

    async def disconnect_all(self) -> None:
        """
        Force disconnect all WebSocket connections

        Called during application shutdown to clean up active connections
        """
        user_ids = list(self.user_connections.keys())
        for user_id in user_ids:
            connections = list(self.user_connections.get(user_id, set()))
            for ws in connections:
                try:
                    await ws.close(
                        code = 1012,
                        reason = "Server reloading"
                    )
                except Exception as e:
                    logger.debug(
                        f"Error closing websocket for user {user_id}: {e}"
                    )

            # Clear subscriptions
            for upload_id in list(self.user_subscriptions.get(user_id,
                                                              [])):
                await self.unsubscribe_upload(user_id, upload_id)

        # Clear all dictionaries
        self.user_connections.clear()
        self.upload_subscribers.clear()
        self.user_subscriptions.clear()

        logger.info("All WebSocket connections closed")


# DI
_manager: ConnectionManager | None = None


def init_manager() -> None:
    """
    Initialize global connection manager
    """
    global _manager
    _manager = ConnectionManager()
    logger.info("ConnectionManager initialized")


def get_manager() -> ConnectionManager:
    """
    Get connection manager instance
    """
    if _manager is None:
        raise RuntimeError(
            "ConnectionManager not initialized. Call init_manager()"
        )
    return _manager
