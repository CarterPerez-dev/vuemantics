"""
ⒸAngelaMos | 2026
search.py
"""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
)

import config
from config import settings
from auth import (
    get_current_user,
    verify_upload_ownership,
)
from core import (
    AUTH_401,
    NOT_FOUND_404,
    RATE_LIMIT_420,
    SERVER_ERROR_500,
    VALIDATION_422,
    ValidationError,
    limiter,
)
from models.Upload import ProcessingStatus, Upload
from models.User import User
from schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from services.search_service import search_service


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/search",
    tags = ["search"],
    responses = {
        **AUTH_401,
        **NOT_FOUND_404,
        **VALIDATION_422,
        **RATE_LIMIT_420,
        **SERVER_ERROR_500,
    },
)


@router.post(
    "",
    response_model = SearchResponse,
    summary = "Search uploads",
    description = "Search through uploads using natural language queries",
)
@limiter.limit(settings.rate_limit_search)
async def search_uploads(
    request: Request,
    search_request: SearchRequest,
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> SearchResponse:
    """
    Perform semantic search on user's uploads

    The search uses AI-generated embeddings to find uploads
    that match the semantic meaning of your query.

    Example queries:
    - "sunset at the beach"
    - "funny cat videos"
    - "birthday party with friends"
    - "cooking in the kitchen"

    Supports filtering by:
    - File type (image/video)
    - Date range
    - Similarity threshold
    """
    try:
        # Log search for analytics (but don't store query for privacy)
        logger.info(
            f"User {current_user.id} searching with "
            f"{len(search_request.query)} char query"
        )

        # Check if user has any uploads
        upload_count = await Upload.count({"user_id": current_user.id})
        if upload_count == 0:
            return SearchResponse(
                results = [],
                total_found = 0,
                returned_count = 0,
                search_time_ms = 0.0,
                query = search_request.query,
                query_embedding_generated = False,
                applied_filters = None,
            )

        # Perform search (limited to user's uploads by default)
        response = await search_service.search(
            request = search_request,
            user_id = current_user.id
        )

        # Log search metrics
        logger.info(
            f"Search completed: {response.returned_count} results "
            f"in {response.search_time_ms:.1f}ms"
        )

        return response

    except Exception as e:
        logger.error(f"Search failed for user {current_user.id}: {e}")
        raise


@router.get(
    "/similar/{upload_id}",
    response_model = list[SearchResult],
    summary = "Find similar uploads",
    description = "Find uploads similar to a specific upload",
)
@limiter.limit(settings.rate_limit_search)
async def find_similar_uploads(
    request: Request,
    upload: Annotated[Upload,
                      Depends(verify_upload_ownership)],
    current_user: Annotated[User,
                            Depends(get_current_user)],
    limit: Annotated[int,
                     Query(ge = 1,
                           le = 50)] = 10,
    include_own: Annotated[
        bool,
        Query(description = "Include your own uploads")] = True,
) -> list[SearchResult]:
    """
    Find uploads similar to a specific upload.

    Uses the embedding of the specified upload to find
    other semantically similar uploads.
    """
    if not upload.embedding_local:
        raise ValidationError("Upload has not been processed yet")

    try:
        # Find similar uploads
        results = await search_service.find_similar_uploads(
            upload = upload,
            user_id = current_user.id,
            limit = limit,
        )

        logger.info(
            f"Found {len(results)} similar uploads for {upload.id}"
        )

        return results

    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        raise


@router.get(
    "/suggestions",
    response_model = list[str],
    summary = "Get search suggestions",
    description = "Get search query suggestions based on partial input",
)
@limiter.limit(settings.rate_limit_common)
async def get_search_suggestions(
    request: Request,
    current_user: Annotated[User,
                            Depends(get_current_user)],
    q: Annotated[str,
                 Query(
                     min_length = 2,
                     max_length = 50,
                     description = "Partial query"
                 )] = "",
) -> list[str]:
    """
    Get search suggestions for autocomplete.

    Returns suggested search queries based on the partial input.
    For MVP, returns template-based suggestions.
    """
    if not q:
        return []

    try:
        suggestions = await search_service.get_search_suggestions(
            partial_query = q,
            user_id = current_user.id,
            limit = config.SEARCH_SUGGESTIONS_DEFAULT_LIMIT
        )

        return suggestions

    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        # Return empty list on error (non-critical feature)
        return []


@router.post(
    "/batch",
    response_model = dict[str,
                          SearchResponse],
    summary = "Batch search",
    description = "Perform multiple searches in one request",
)
@limiter.limit(settings.rate_limit_search)
async def batch_search(
    request: Request,
    current_user: Annotated[User,
                            Depends(get_current_user)],
    queries: list[str] = Query(
        ...,
        max_items = 5,
        description = "List of search queries"
    ),
) -> dict[str,
          SearchResponse]:
    """
    Perform multiple searches in a single request.

    Useful for comparing results across different queries
    or pre-loading search results.

    Limited to 5 queries per request.
    """
    if not queries:
        return {}

    try:
        # Perform batch search (validation happens in SearchRequest schema)
        results = await search_service.batch_search(
            queries = queries,
            user_id = current_user.id,
            max_concurrent = config.BATCH_SEARCH_MAX_CONCURRENT
        )

        logger.info(f"Batch search completed for {len(queries)} queries")

        return results

    except Exception as e:
        logger.error(f"Batch search failed: {e}")
        raise


@router.get(
    "/stats",
    summary = "Get search statistics",
    description = "Get statistics about searchable content",
)
async def get_search_stats(
    current_user: Annotated[User,
                            Depends(get_current_user)],
) -> dict:
    """
    Get statistics about searchable uploads.

    Returns counts of processed uploads ready for search.
    """
    try:
        # Get upload counts by status
        counts = await Upload.count_by_user(current_user.id)

        # Count uploads with embeddings
        total_searchable = counts.get(ProcessingStatus.COMPLETED, 0)
        total_processing = (
            counts.get(ProcessingStatus.PENDING,
                       0) + counts.get(ProcessingStatus.ANALYZING,
                                       0) +
            counts.get(ProcessingStatus.EMBEDDING,
                       0)
        )
        total_failed = counts.get(ProcessingStatus.FAILED, 0)

        return {
            "total_uploads": sum(counts.values()),
            "searchable_uploads": total_searchable,
            "processing_uploads": total_processing,
            "failed_uploads": total_failed,
            "stats_by_status": counts,
        }

    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise
