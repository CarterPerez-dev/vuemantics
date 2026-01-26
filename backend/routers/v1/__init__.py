"""
ⒸAngelaMos | 2026
API v1 routers
"""

from fastapi import APIRouter

from . import (
    auth,
    client_config,
    health,
    upload,
    search,
)


router = APIRouter()

router.include_router(auth.router, tags = ["auth"])
router.include_router(client_config.router, tags = ["config"])
router.include_router(health.router, tags = ["health"])
router.include_router(upload.router, tags = ["uploads"])
router.include_router(search.router, tags = ["search"])

__all__ = [
    "router",
    "auth",
    "client_config",
    "health",
    "upload",
    "search",
]
