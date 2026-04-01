"""
©AngelaMos | 2026
settings.py
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import database
from auth import get_current_user
from models.User import User
from services.ai.providers.factory import get_provider, set_provider
from workers.reembed_task import reembed_all


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings")


class ProviderResponse(BaseModel):
    provider: str
    local_count: int
    gemini_count: int


class SetProviderRequest(BaseModel):
    provider: str


class ReembedResponse(BaseModel):
    status: str
    message: str


@router.get("/provider", response_model=ProviderResponse)
async def get_provider_settings(
    current_user: User = Depends(get_current_user),
) -> ProviderResponse:
    provider = await get_provider()

    local_count = await database.db.fetchval(
        "SELECT COUNT(*) FROM uploads WHERE embedding_local IS NOT NULL"
    ) or 0
    gemini_count = await database.db.fetchval(
        "SELECT COUNT(*) FROM uploads WHERE embedding_gemini IS NOT NULL"
    ) or 0

    return ProviderResponse(
        provider=provider.provider_name,
        local_count=int(local_count),
        gemini_count=int(gemini_count),
    )


@router.post("/provider", response_model=ProviderResponse)
async def update_provider(
    body: SetProviderRequest,
    current_user: User = Depends(get_current_user),
) -> ProviderResponse:
    if body.provider not in ("local", "gemini"):
        raise HTTPException(
            status_code=400, detail="provider must be 'local' or 'gemini'"
        )

    await set_provider(body.provider)
    provider = await get_provider()

    local_count = await database.db.fetchval(
        "SELECT COUNT(*) FROM uploads WHERE embedding_local IS NOT NULL"
    ) or 0
    gemini_count = await database.db.fetchval(
        "SELECT COUNT(*) FROM uploads WHERE embedding_gemini IS NOT NULL"
    ) or 0

    return ProviderResponse(
        provider=provider.provider_name,
        local_count=int(local_count),
        gemini_count=int(gemini_count),
    )


@router.post("/reembed", response_model=ReembedResponse)
async def trigger_reembed(
    current_user: User = Depends(get_current_user),
) -> ReembedResponse:
    reembed_all.send(str(current_user.id))
    return ReembedResponse(
        status="queued",
        message="Re-embed job queued. Progress will appear via WebSocket.",
    )
