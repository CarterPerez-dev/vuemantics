"""
Search routes for semantic similarity search.

Implements natural language search over uploaded media using
vector embeddings and pgvector. Supports filtering and finding
similar uploads.
---
/backend/routers/search.py
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_current_user
from models import Upload, User
from schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from services import search_service

logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={
        401: {"description": "Unauthorized"},
        429: {"description": "Too many requests"},
    },
)


@router.post(
    "",
    response_model=SearchResponse,
    summary="Search uploads",
    description="Search through uploads using natural language queries",
)
@limiter.limit("60/minute")
async def search_uploads(
    request: Request,
    search_request: SearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SearchResponse:
    """
    Perform semantic search on user's uploads.

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
                results=[],
                total_found=0,
                returned_count=0,
                search_time_ms=0.0,
                query=search_request.query,
                query_embedding_generated=False,
                applied_filters=None,
            )

        # Perform search (limited to user's uploads by default)
        response = await search_service.search(
            request=search_request, user_id=current_user.id
        )

        # Log search metrics
        logger.info(
            f"Search completed: {response.returned_count} results "
            f"in {response.search_time_ms:.1f}ms"
        )

        return response

    except Exception as e:
        logger.error(f"Search failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service temporarily unavailable",
        ) from e


@router.get(
    "/similar/{upload_id}",
    response_model=list[SearchResult],
    summary="Find similar uploads",
    description="Find uploads similar to a specific upload",
)
@limiter.limit("30/minute")
async def find_similar_uploads(
    request: Request,
    upload_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    include_own: Annotated[bool, Query(description="Include your own uploads")] = True,
) -> list[SearchResult]:
    """
    Find uploads similar to a specific upload.

    Uses the embedding of the specified upload to find
    other semantically similar uploads.
    """
    # Verify upload exists and belongs to user
    upload = await Upload.find_by_id(upload_id)
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found"
        )

    if upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found"
        )

    if not upload.embedding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload has not been processed yet",
        )

    try:
        # Find similar uploads
        results = await search_service.find_similar_uploads(
            upload_id=upload_id,
            user_id=current_user.id,
            limit=limit,
            include_same_user=include_own,
        )

        logger.info(f"Found {len(results)} similar uploads for {upload_id}")

        return results

    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service temporarily unavailable",
        ) from e


@router.get(
    "/suggestions",
    response_model=list[str],
    summary="Get search suggestions",
    description="Get search query suggestions based on partial input",
)
@limiter.limit("100/minute")
async def get_search_suggestions(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    q: Annotated[
        str, Query(min_length=2, max_length=50, description="Partial query")
    ] = "",
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
            partial_query=q, user_id=current_user.id, limit=5
        )

        return suggestions

    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        # Return empty list on error (non-critical feature)
        return []


@router.post(
    "/batch",
    response_model=dict[str, SearchResponse],
    summary="Batch search",
    description="Perform multiple searches in one request",
)
@limiter.limit("10/minute")
async def batch_search(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    queries: list[str] = Query(..., max_items=5, description="List of search queries"),
) -> dict[str, SearchResponse]:
    """
    Perform multiple searches in a single request.

    Useful for comparing results across different queries
    or pre-loading search results.

    Limited to 5 queries per request.
    """
    if not queries:
        return {}

    try:
        # Query length limits
        MIN_QUERY_LENGTH = 1
        MAX_QUERY_LENGTH = 500

        # Validate queries
        for query in queries:
            if len(query) < MIN_QUERY_LENGTH or len(query) > MAX_QUERY_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Query must be 1-500 characters: {query[:50]}...",
                )

        # Perform batch search
        results = await search_service.batch_search(
            queries=queries, user_id=current_user.id, max_concurrent=3
        )

        logger.info(f"Batch search completed for {len(queries)} queries")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service temporarily unavailable",
        ) from e


@router.get(
    "/stats",
    summary="Get search statistics",
    description="Get statistics about searchable content",
)
async def get_search_stats(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Get statistics about searchable uploads.

    Returns counts of processed uploads ready for search.
    """
    try:
        # Get upload counts by status
        counts = await Upload.count_by_user(current_user.id)

        # Count uploads with embeddings
        total_searchable = counts.get("completed", 0)
        total_processing = (
            counts.get("pending", 0)
            + counts.get("analyzing", 0)
            + counts.get("embedding", 0)
        )
        total_failed = counts.get("failed", 0)

        return {
            "total_uploads": sum(counts.values()),
            "searchable_uploads": total_searchable,
            "processing_uploads": total_processing,
            "failed_uploads": total_failed,
            "stats_by_status": counts,
        }

    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        ) from e
