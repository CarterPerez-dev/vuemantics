"""
©AngelaMos | 2026
settings.py
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import config
import database
from auth import get_current_admin_user
from core import ValidationError
from models.User import User
from services.ai.providers.factory import get_provider, set_provider
from workers.reembed_task import reembed_all


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings")


class GeminiCostEstimate(BaseModel):
    cost_per_image: float
    cost_per_video_frame: float
    max_frames_per_video: int
    max_cost_per_video: float
    gemini_image_count: int
    gemini_video_count: int
    estimated_image_cost: float
    estimated_video_cost: float
    estimated_total_cost: float


class ProviderResponse(BaseModel):
    provider: str
    local_count: int
    gemini_count: int
    cost_estimate: GeminiCostEstimate | None = None


class SetProviderRequest(BaseModel):
    provider: str


class ReembedResponse(BaseModel):
    status: str
    message: str


async def _build_provider_response(provider_name: str) -> ProviderResponse:
    row = await database.db.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE embedding_local IS NOT NULL) AS local_count,
            COUNT(*) FILTER (WHERE embedding_gemini IS NOT NULL) AS gemini_count,
            COUNT(*) FILTER (WHERE embedding_gemini IS NOT NULL AND file_type = 'image') AS gemini_images,
            COUNT(*) FILTER (WHERE embedding_gemini IS NOT NULL AND file_type = 'video') AS gemini_videos
        FROM uploads
        """
    )

    local_count = int(row["local_count"])
    gemini_count = int(row["gemini_count"])
    gemini_images = int(row["gemini_images"])
    gemini_videos = int(row["gemini_videos"])

    max_cost_per_video = config.GEMINI_EMBEDDING_MAX_VIDEO_FRAMES * config.GEMINI_COST_PER_VIDEO_FRAME
    estimated_image_cost = round(gemini_images * config.GEMINI_COST_PER_IMAGE, 6)
    estimated_video_cost = round(gemini_videos * max_cost_per_video, 6)

    cost_estimate = GeminiCostEstimate(
        cost_per_image=config.GEMINI_COST_PER_IMAGE,
        cost_per_video_frame=config.GEMINI_COST_PER_VIDEO_FRAME,
        max_frames_per_video=config.GEMINI_EMBEDDING_MAX_VIDEO_FRAMES,
        max_cost_per_video=round(max_cost_per_video, 5),
        gemini_image_count=gemini_images,
        gemini_video_count=gemini_videos,
        estimated_image_cost=estimated_image_cost,
        estimated_video_cost=estimated_video_cost,
        estimated_total_cost=round(estimated_image_cost + estimated_video_cost, 6),
    )

    return ProviderResponse(
        provider=provider_name,
        local_count=local_count,
        gemini_count=gemini_count,
        cost_estimate=cost_estimate,
    )


@router.get("/provider", response_model=ProviderResponse)
async def get_provider_settings(
    current_user: User = Depends(get_current_admin_user),
) -> ProviderResponse:
    provider = await get_provider()
    return await _build_provider_response(provider.provider_name)


@router.post("/provider", response_model=ProviderResponse)
async def update_provider(
    body: SetProviderRequest,
    current_user: User = Depends(get_current_admin_user),
) -> ProviderResponse:
    if body.provider not in ("local", "gemini"):
        raise ValidationError("provider must be 'local' or 'gemini'")

    await set_provider(body.provider)
    provider = await get_provider()
    return await _build_provider_response(provider.provider_name)


@router.post("/reembed", response_model=ReembedResponse)
async def trigger_reembed(
    current_user: User = Depends(get_current_admin_user),
) -> ReembedResponse:
    reembed_all.send(str(current_user.id))
    return ReembedResponse(
        status="queued",
        message="Re-embed job queued. Progress will appear via WebSocket.",
    )
