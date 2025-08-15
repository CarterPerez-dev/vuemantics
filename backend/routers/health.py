"""
Health check endpoints for monitoring and status verification.

Provides endpoints to check application health, database connectivity,
and future service availability (Redis, AI services, storage).
---
/backend/routers/health.py
"""

import logging
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from config import settings
from database import db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["system"],
    responses={
        503: {"description": "Service Unavailable"},
    },
)


@router.get(
    "",
    summary="Health Check",
    description="Check application and database health",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "environment": "development",
                        "database": "connected",
                        "version": "0.1.0",
                    }
                }
            },
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "environment": "development",
                        "version": "0.1.0",
                        "checks": {"database": "unhealthy"},
                    }
                }
            },
        },
    },
)
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for monitoring.

    Checks:
    - Database connectivity
    - Future: Redis connection
    - Future: AI service availability
    - Future: Storage availability
    """
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
        "checks": {},
    }

    try:
        await db.fetchval("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "unhealthy"

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status
        )

    # Future checks:
    # - Redis connection
    # - AI service availability
    # - Storage availability

    return health_status


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the service is ready to handle requests",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness_check() -> dict[str, Any]:
    """
    Readiness probe for Kubernetes-style deployments.
    """
    ready_status = {"ready": True, "checks": {}}

    try:
        count = await db.fetchval("SELECT COUNT(*) FROM users")
        ready_status["checks"]["database"] = "ready"
        ready_status["checks"]["users_table"] = f"{count} users"
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        ready_status["ready"] = False
        ready_status["checks"]["database"] = f"error: {e!s}"

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=ready_status
        )

    # Future readiness checks:
    # - Redis is accepting connections
    # - AI API keys are valid
    # - Storage directory is writable
    # - Required environment variables are set

    return ready_status


@router.get(
    "/live",
    summary="Liveness Check",
    description="Simple check to verify the service is alive",
    responses={
        200: {"description": "Service is alive"},
    },
)
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe for Kubernetes-style deployments.

    Very simple check - just returns 200 if the service is running.
    Used to detect if the service needs to be restarted.
    """
    return {"status": "alive"}
