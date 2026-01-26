"""
ⒸAngelaMos | 2026
Health check schemas
"""

from enum import Enum

from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field,
)


class HealthStatus(str, Enum):
    """
    Health status values
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthDetailedResponse(BaseModel):
    """
    Detailed health check response
    """
    model_config = ConfigDict(
        extra = "forbid",
        use_enum_values = True,
    )

    status: HealthStatus = Field(description = "Overall health status")
    environment: str = Field(description = "Current environment")
    version: str = Field(description = "Application version")
    database: HealthStatus = Field(description = "Database health status")
    redis: HealthStatus | None = Field(
        default = None,
        description = "Redis health status"
    )
    ollama: HealthStatus | None = Field(
        default = None,
        description = "Ollama AI service health status"
    )
