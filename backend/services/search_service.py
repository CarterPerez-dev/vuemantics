"""
Search service for semantic similarity search using embeddings.

Handles query embedding generation, vector search orchestration,
and result formatting. Uses OpenAI for query embeddings and
pgvector for similarity search.
---
/backend/services/search_service.py
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI

from config import settings
from models import Upload
from schemas import SearchRequest, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class SearchServiceError(Exception):
    """
    Base exception for search service errors.
    """

    pass


class QueryEmbeddingError(SearchServiceError):
    """
    Raised when query embedding generation fails.
    """

    pass


class SearchService:
    """
    Handles semantic search functionality.

    Workflow:
    1. Generate embedding for search query
    2. Find similar uploads using pgvector
    3. Apply additional filters
    4. Format and return results
    """

    def __init__(self):
        """
        Initialize search service with OpenAI client.
        """
        self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._embedding_model = settings.embedding_model
        logger.info("Search service initialized")

    async def search(
        self, request: SearchRequest, user_id: UUID | None = None
    ) -> SearchResponse:
        """
        Perform semantic search on uploads.

        Args:
            request: Search parameters including query and filters
            user_id: Optional user ID to limit search scope

        Returns:
            SearchResponse with ranked results
        """
        start_time = time.time()

        try:
            # Generate embedding for search query
            logger.info(f"Generating embedding for query: {request.query[:50]}...")
            query_embedding = await self._generate_query_embedding(request.query)

            # Perform vector similarity search
            results = await self._search_uploads(
                query_embedding=query_embedding,
                user_id=user_id if request.user_id is None else request.user_id,
                limit=request.limit * 2,  # Get extra for post-filtering
                similarity_threshold=request.similarity_threshold,
            )

            # Apply additional filters
            filtered_results = self._apply_filters(results, request)

            # Limit to requested count
            final_results = filtered_results[: request.limit]

            # Format response
            search_time_ms = (time.time() - start_time) * 1000

            response = SearchResponse(
                results=final_results,
                total_found=len(filtered_results),
                returned_count=len(final_results),
                search_time_ms=search_time_ms,
                query=request.query,
                query_embedding_generated=True,
                applied_filters=self._get_applied_filters(request),
            )

            logger.info(
                f"Search completed: {len(final_results)} results in {search_time_ms:.1f}ms"
            )
            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Return empty results with error indication
            search_time_ms = (time.time() - start_time) * 1000
            return SearchResponse(
                results=[],
                total_found=0,
                returned_count=0,
                search_time_ms=search_time_ms,
                query=request.query,
                query_embedding_generated=False,
                applied_filters=None,
            )

    async def _generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding vector for search query.

        Args:
            query: Search query text

        Returns:
            1536-dimensional embedding vector

        Raises:
            QueryEmbeddingError: If embedding generation fails
        """
        try:
            # Clean query
            cleaned_query = " ".join(query.split())

            # Enhance query for better search results
            enhanced_query = f"Find media content related to: {cleaned_query}"

            # Generate embedding
            response = await self._openai_client.embeddings.create(
                input=enhanced_query,
                model=self._embedding_model,
                encoding_format="float",
            )

            embedding = response.data[0].embedding

            if len(embedding) != settings.embedding_dimensions:
                raise QueryEmbeddingError(
                    f"Invalid embedding dimensions: {len(embedding)}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Query embedding generation failed: {e}")
            raise QueryEmbeddingError(f"Failed to generate embedding: {e!s}") from e

    async def _search_uploads(
        self,
        query_embedding: list[float],
        user_id: UUID | None,
        limit: int,
        similarity_threshold: float,
    ) -> list[SearchResult]:
        """
        Search uploads using vector similarity.

        Args:
            query_embedding: Query embedding vector
            user_id: Optional user filter
            limit: Maximum results
            similarity_threshold: Minimum similarity

        Returns:
            List of search results with similarity scores
        """
        # Perform vector search
        upload_results = await Upload.search_by_embedding(
            query_embedding=query_embedding,
            user_id=user_id,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )

        # Convert to SearchResult objects
        search_results = []
        for rank, (upload, similarity) in enumerate(upload_results, 1):
            # Calculate distance (1 - similarity for cosine)
            distance = 1.0 - similarity

            result = SearchResult(
                upload=upload.to_dict(),
                similarity_score=similarity,
                distance=distance,
                rank=rank,
            )
            search_results.append(result)

        return search_results

    def _apply_filters(
        self, results: list[SearchResult], request: SearchRequest
    ) -> list[SearchResult]:
        """
        Apply additional filters to search results.

        Args:
            results: Initial search results
            request: Search request with filters

        Returns:
            Filtered results
        """
        filtered = results

        # Filter by file types
        if request.file_types:
            filtered = [
                r for r in filtered if r.upload.get("file_type") in request.file_types
            ]

        # Filter by date range
        if request.date_from:
            filtered = [
                r
                for r in filtered
                if datetime.fromisoformat(r.upload.get("created_at", ""))
                >= request.date_from
            ]

        if request.date_to:
            filtered = [
                r
                for r in filtered
                if datetime.fromisoformat(r.upload.get("created_at", ""))
                <= request.date_to
            ]

        # Re-rank after filtering
        for rank, result in enumerate(filtered, 1):
            result.rank = rank

        return filtered

    def _get_applied_filters(self, request: SearchRequest) -> dict[str, Any] | None:
        """
        Get summary of applied filters.

        Args:
            request: Search request

        Returns:
            Dictionary of applied filters or None
        """
        filters = {}

        if request.file_types:
            filters["file_types"] = request.file_types

        if request.date_from:
            filters["date_from"] = request.date_from.isoformat()

        if request.date_to:
            filters["date_to"] = request.date_to.isoformat()

        if request.similarity_threshold > 0:
            filters["similarity_threshold"] = request.similarity_threshold

        return filters if filters else None

    async def find_similar_uploads(
        self,
        upload_id: UUID,
        user_id: UUID,
        limit: int = 10,
        include_same_user: bool = True,
    ) -> list[SearchResult]:
        """
        Find uploads similar to a specific upload.

        Args:
            upload_id: Upload to find similar items for
            user_id: Current user ID
            limit: Maximum results
            include_same_user: Whether to include user's own uploads

        Returns:
            List of similar uploads
        """
        # Get the upload
        upload = await Upload.find_by_id(upload_id)
        if not upload or upload.user_id != user_id:
            return []

        if not upload.embedding:
            logger.warning(f"Upload {upload_id} has no embedding")
            return []

        # Search using the upload's embedding
        search_user_id = None if include_same_user else user_id
        results = await self._search_uploads(
            query_embedding=upload.embedding,
            user_id=search_user_id,
            limit=limit + 1,  # Get extra to exclude self
            similarity_threshold=0.5,
        )

        # Exclude the source upload
        filtered_results = [r for r in results if r.upload.get("id") != str(upload_id)]

        return filtered_results[:limit]

    async def batch_search(
        self, queries: list[str], user_id: UUID | None = None, max_concurrent: int = 3
    ) -> dict[str, SearchResponse]:
        """
        Perform multiple searches concurrently.

        Args:
            queries: List of search queries
            user_id: Optional user filter
            max_concurrent: Maximum concurrent searches

        Returns:
            Dictionary mapping queries to results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def search_with_limit(query: str) -> tuple[str, SearchResponse]:
            async with semaphore:
                request = SearchRequest(query=query, limit=10)
                result = await self.search(request, user_id)
                return query, result

        # Execute searches concurrently
        tasks = [search_with_limit(query) for query in queries]
        results = await asyncio.gather(*tasks)

        return dict(results)

    async def get_search_suggestions(
        self, partial_query: str, user_id: UUID, limit: int = 5  # noqa: ARG002
    ) -> list[str]:
        """
        Get search suggestions based on partial query.

        For MVP, this returns common search patterns.
        In production, could use search history or popular searches.

        Args:
            partial_query: Partial search query
            user_id: User ID
            limit: Maximum suggestions

        Returns:
            List of suggested queries
        """
        # MVP: Return template-based suggestions
        templates = [
            f"{partial_query} photos",
            f"{partial_query} videos",
            f"{partial_query} at night",
            f"{partial_query} with friends",
            f"{partial_query} outdoor",
            f"funny {partial_query}",
            f"{partial_query} selfie",
            f"{partial_query} landscape",
        ]

        # Filter relevant templates
        suggestions = [t for t in templates if partial_query.lower() in t.lower()]

        return suggestions[:limit]

    def calculate_embedding_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        # Simple dot product for normalized vectors
        # (OpenAI embeddings are pre-normalized)
        similarity = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
        return max(0.0, min(1.0, similarity))


# Global instance
search_service = SearchService()
