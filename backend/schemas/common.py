"""
ⒸAngelaMos | 2026
common.py - Common/generic schemas
"""

from pydantic import BaseModel


class AppInfoResponse(BaseModel):
    """
    Root endpoint response with API information
    """
    name: str
    version: str
    environment: str
    documentation: str
