"""
Routers package for FastAPI endpoints.
"""

from . import (
    auth, 
    health, 
    upload, 
    search,
)

__all__ = [
    "auth",
    "health",
    "upload",
    "search",
]
