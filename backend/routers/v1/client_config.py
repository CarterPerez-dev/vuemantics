"""
ⒸAngelaMos | 2026
client_config.py - Client configuration endpoint
"""

import logging

from fastapi import APIRouter, Request, status

import config
from config import settings
from core import RATE_LIMIT_420, SERVER_ERROR_500, limiter
from schemas.client_config import ClientConfigResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/client-config",
    tags = ["client-config"],
    responses = {
        **RATE_LIMIT_420,
        **SERVER_ERROR_500,
    },
)


@router.get(
    "",
    response_model = ClientConfigResponse,
    status_code = status.HTTP_200_OK,
    summary = "Get client configuration",
    description = "Public endpoint for frontend configuration constants",
)
@limiter.limit(settings.rate_limit_common)
async def get_client_config(request: Request) -> ClientConfigResponse:
    """
    Get client configuration values for frontend.

    Returns configuration constants that clients need,
    making backend the source of truth.

    This is a public endpoint (no authentication required).
    """
    try:
        return ClientConfigResponse(
            search_default_similarity_threshold = config.
            SEARCH_DEFAULT_SIMILARITY_THRESHOLD,
            similar_uploads_similarity_threshold = config.
            SIMILAR_UPLOADS_SIMILARITY_THRESHOLD,
            similar_uploads_default_limit = config.
            SIMILAR_UPLOADS_DEFAULT_LIMIT,
            max_query_length = config.MAX_QUERY_LENGTH,
            default_page_size = config.DEFAULT_PAGE_SIZE,
            max_page_size = config.MAX_PAGE_SIZE,
            max_upload_size_mb = config.settings.max_upload_size //
            (1024 * 1024),
        )
    except Exception as e:
        logger.error(f"Failed to load client config: {e}")
        raise
