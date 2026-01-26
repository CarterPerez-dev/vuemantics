"""
Routers package for FastAPI endpoints.
"""

from . import (
    auth,
    client_config,
    health,
    upload,
    search,
    websocket,
)


__all__ = [
    "auth",
    "client_config",
    "health",
    "upload",
    "search",
    "websocket",
]
