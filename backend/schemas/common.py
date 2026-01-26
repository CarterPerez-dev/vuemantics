"""
ⒸAngelaMos | 2026
common.py - Common/generic schemas
"""

from pydantic import BaseModel, ConfigDict


class AppInfoResponse(BaseModel):
    """
    Root endpoint response with API information
    """
    model_config = ConfigDict(
        extra = "forbid",
    )

    name: str
    version: str
    environment: str
    documentation: str
