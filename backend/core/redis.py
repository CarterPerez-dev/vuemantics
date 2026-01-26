"""
ⒸAngelaMos | 2026
redis.py
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import redis.asyncio as redis

import config


logger = logging.getLogger(__name__)


class RedisPool:
    """
    Manages Redis connection pool for caching and pub/sub

    Provides methods for caching operations and pub/sub messaging
    Used for WebSocket cross-instance communication
    """
    def __init__(self) -> None:
        """
        Initialize Redis pool instance
        """
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """
        Initialize Redis connection pool
        """
        if self._pool is not None:
            return

        async with self._lock:
            if self._pool is not None:
                return

            try:
                self._pool = redis.ConnectionPool.from_url(
                    config.settings.redis_url,
                    decode_responses = config.settings.
                    redis_decode_responses,
                    max_connections = config.settings.redis_pool_max_size,
                )

                self._client = redis.Redis(connection_pool = self._pool)

                await self._client.ping()

                logger.info(
                    "Redis pool created successfully",
                    extra = {
                        "max_connections":
                        config.settings.redis_pool_max_size,
                    },
                )

            except Exception as e:
                logger.error(f"Failed to create Redis pool: {e}")
                raise

    async def disconnect(self) -> None:
        """
        Close all Redis connections
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None

        logger.info("Redis pool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[redis.Redis]:
        """
        Acquire a Redis connection from the pool
        """
        if self._client is None:
            raise RuntimeError(
                "Redis pool is not initialized. Call connect() first."
            )

        yield self._client

    async def publish(self, channel: str, message: str) -> int:
        """
        Publish message to Redis channel

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers that received the message
        """
        async with self.acquire() as client:
            return await client.publish(channel, message)

    async def subscribe(self, *channels: str) -> redis.client.PubSub:
        """
        Subscribe to Redis channels

        Args:
            channels: Channel names to subscribe to

        Returns:
            PubSub object for receiving messages
        """
        if self._client is None:
            raise RuntimeError("Redis pool is not initialized")

        pubsub = self._client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def psubscribe(self, *patterns: str) -> redis.client.PubSub:
        """
        Subscribe to Redis channel patterns

        Args:
            patterns: Channel patterns to subscribe to (e.g., "upload:*")

        Returns:
            PubSub object for receiving messages
        """
        if self._client is None:
            raise RuntimeError("Redis pool is not initialized")

        pubsub = self._client.pubsub()
        await pubsub.psubscribe(*patterns)
        return pubsub

    @property
    def client(self) -> redis.Redis | None:
        """
        Get the Redis client
        """
        return self._client


redis_pool = RedisPool()


async def init_redis() -> None:
    """
    Initialize Redis connection pool

    Should be called during application startup
    """
    await redis_pool.connect()


async def close_redis() -> None:
    """
    Close Redis connection pool

    Should be called during application shutdown
    """
    await redis_pool.disconnect()
