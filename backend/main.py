"""
ⒸAngelaMos | 2026
main.py
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler

import config
from core import (
    BaseAppException,
    CorrelationIdMiddleware,
    RateLimitExceeded,
    limiter,
)
from database import close_db, db, init_db
from routers import (
    auth,
    client_config,
    health,
    search,
    upload,
)

# logging
logging.basicConfig(
    level = logging.INFO if not config.settings.debug else logging.DEBUG,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application lifecycle.

    Handles startup and shutdown events for database connections
    and any other resources that need initialization/cleanup.
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

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connection pool closed")


# FastAPI instance
app = FastAPI(
    title = config.settings.app_name,
    description =
    "Vector multimodal search for your personal media collection",
    version = config.APP_VERSION,
    lifespan = lifespan,
    docs_url = "/docs",
    redoc_url = "/redoc",
    openapi_url = "/openapi.json",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


@app.exception_handler(BaseAppException)
async def app_exception_handler(
    _request: Request,
    exc: BaseAppException,
) -> JSONResponse:
    """
    Handle all application exceptions.
    """
    return JSONResponse(
        status_code = exc.status_code,
        content = {
            "detail": exc.message,
            "type": exc.__class__.__name__,
        },
    )


# Middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins = config.settings.cors_origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
    expose_headers = ["X-Correlation-ID"],
)


@app.get(
    "/",
    summary = "API Root",
    description = "One is None",
    tags = ["system"],
)
async def root() -> dict[str, Any]:
    """
    Root endpoint with API information
    """
    return {
        "name": config.settings.app_name,
        "version": config.APP_VERSION,
        "environment": config.settings.environment,
        "documentation": "/docs",
    }

# Routers
app.include_router(auth.router)
app.include_router(client_config.router)
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(search.router)

# Dev only endpoints
if config.settings.is_development:

    @app.get("/api/debug/settings", tags = ["debug"])
    async def debug_settings() -> dict[str, Any]:
        """
        Show current settings (dev)
        """
        safe_settings = {
            "app_name": config.settings.app_name,
            "environment": config.settings.environment,
            "debug": config.settings.debug,
            "database_url": "***hidden***",
            "cors_origins": config.settings.cors_origins,
            "upload_path": str(config.settings.upload_path),
            "max_upload_size": config.settings.max_upload_size,
            "allowed_mime_types": list(config.settings.allowed_mime_types),
        }
        return safe_settings
