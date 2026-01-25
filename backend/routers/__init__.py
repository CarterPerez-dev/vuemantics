"""
Routers package for FastAPI endpoints.
"""

from . import (
    auth,
    client_config,
    health,
    upload,
    search,
)


__all__ = [
    "auth",
    "client_config",
    "health",
    "upload",
    "search",
]
