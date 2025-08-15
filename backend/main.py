"""
Main FastAPI application entry point.

Configures the app with middleware, routers, and lifecycle events.
Handles database connections, CORS, rate limiting, and error handling.
---
/backend/main.py
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from database import close_db, db, init_db
from routers import (
    auth,
    health,
    search,
    upload,
)

# logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Manage application lifecycle.

    Handles startup and shutdown events for database connections
    and any other resources that need initialization/cleanup.
    """
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")

    try:
        await init_db()
        logger.info("Database connection pool initialized")

        version = await db.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        )
        if version:
            logger.info(f"pgvector {version} is ready")
        else:
            logger.warning("pgvector extension not found - vector search will fail")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connection pool closed")


# FastAPI instance
app = FastAPI(
    title=settings.app_name,
    description="Vector multimodal search for your personal media collection",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

# Exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """
    Handle validation errors with clean error messages.
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"][1:]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """
    Catch-all exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    detail = str(exc) if settings.is_development else "An internal error occurred"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": detail}
    )


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Add unique request ID for tracking requests through logs.
    """
    request_id = str(uuid4())

    request.state.request_id = request_id

    start_time = time.time()
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"Request {request_id} completed: "
        f"status={response.status_code} time={process_time:.3f}s"
    )

    response.headers["X-Request-ID"] = request_id
    return response


# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(search.router, prefix="/api")


# Root endpoint
@app.get(
    "/",
    summary="API Root",
    description="Get basic API information",
    tags=["system"],
)
async def root() -> dict[str, Any]:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "environment": settings.environment,
        "status": "online",
        "documentation": "/docs" if settings.is_development else None,
        "endpoints": {
            "auth": "/api/auth",
            "health": "/api/health",
            "uploads": "/api/uploads",
            "search": "/api/search",
        },
    }


# Dev only endpoints
if settings.is_development:

    @app.get("/api/debug/settings", tags=["debug"])
    async def debug_settings() -> dict[str, Any]:
        """
        Show current settings (dev).
        """
        safe_settings = {
            "app_name": settings.app_name,
            "environment": settings.environment,
            "debug": settings.debug,
            "database_url": "***hidden***",
            "cors_origins": settings.cors_origins,
            "upload_path": str(settings.upload_path),
            "max_upload_size": settings.max_upload_size,
            "allowed_mime_types": list(settings.allowed_mime_types),
        }
        return safe_settings
