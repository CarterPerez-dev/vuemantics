"""
ⒸAngelaMos | 2026
health.py
"""

import logging

import redis.asyncio as redis
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

import config
from config import settings
from database import db
from schemas import HealthDetailedResponse, HealthStatus


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/health",
    tags = ["system"],
)


@router.get(
    "",
    summary = "Health Check",
    description = "Minimal health check endpoint",
    response_class = PlainTextResponse,
)
async def health_check() -> str:
    """
    Smallest possible byte
    """
    return "1"


@router.get(
    "/detailed",
    response_model = HealthDetailedResponse,
    summary = "Detailed Health Check",
    description = "Detailed application and database health check",
)
async def detailed_health_check() -> HealthDetailedResponse:
    """
    Detailed health check including database connectivity

    healthy, degraded, or unhealthy
    """
    db_status = HealthStatus.UNHEALTHY
    redis_status = None

    try:
        await db.fetchval("SELECT 1")
        db_status = HealthStatus.HEALTHY
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = HealthStatus.UNHEALTHY

    if settings.redis_url:
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                decode_responses = settings.redis_decode_responses
            )
            await redis_client.ping()
            await redis_client.close()
            redis_status = HealthStatus.HEALTHY
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_status = HealthStatus.UNHEALTHY

    services = [db_status,
                redis_status] if redis_status is not None else [db_status]
    healthy_count = sum(1 for s in services if s == HealthStatus.HEALTHY)

    if healthy_count == len(services):
        overall = HealthStatus.HEALTHY
    elif healthy_count > 0:
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.UNHEALTHY

    return HealthDetailedResponse(
        status = overall,
        environment = settings.environment,
        version = config.APP_VERSION,
        database = db_status,
        redis = redis_status,
    )
