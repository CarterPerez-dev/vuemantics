"""
ⒸAngelaMos | 2026
lifespan.py
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import config
from core.redis import close_redis, init_redis, redis_pool
from core.websocket.manager import get_manager, init_manager
from core.websocket.publisher import get_publisher, init_publisher
from database import close_db, db, init_db


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application lifecycle

    Handles startup and shutdown events for database connections
    and any other resources that need initialization/cleanup
    """
    logger.info(
        f"Starting {config.settings.app_name} in {config.settings.environment} mode"
    )

    try:
        await init_db()
        logger.info("Database connection pool initialized")

        version = await db.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        )
        if version:
            logger.info(f"pgvector {version} is ready")
        else:
            logger.warning(
                "pgvector extension not found - vector search will fail"
            )

        await init_redis()
        logger.info("Redis connection pool initialized")

        await redis_pool.client.ping() # type: ignore[union-attr]
        logger.info("Redis is ready")

        init_manager()
        init_publisher()

        await get_publisher().start()
        logger.info("WebSocket publisher started")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info("Shutting down application")

    await get_manager().disconnect_all()
    logger.info("All WebSocket connections closed")

    await get_publisher().stop()
    logger.info("WebSocket publisher stopped")

    await close_redis()
    logger.info("Redis connection pool closed")

    await close_db()
    logger.info("Database connection pool closed")
    
