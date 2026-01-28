"""
ⒸAngelaMos | 2026
search_service.py
"""

import time
import asyncio
import logging
from uuid import UUID
from typing import Any

import config
from core import (
    QueryEmbeddingError,
)
from models.Upload import Upload
from schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from services.ai import local_ai_service


logger = logging.getLogger(__name__)


class SearchService:
    """
    Handles semantic search functionality

    Workflow:
    1. Generate embedding for search query using local bge-m3
    2. Find similar uploads using pgvector
    3. Apply additional filters
    4. Format and return results
    """
    def __init__(self) -> None:
        """
        Initialize search service
        """
        logger.info("Search service initialized")

    async def search(
        self,
        request: SearchRequest,
        user_id: UUID | None = None
    ) -> SearchResponse:
        """
        Perform semantic search on uploads

        Args:
            request: Search parameters including query and filters
            user_id: Optional user ID to limit search scope

        Returns:
            SearchResponse with ranked results
        """
        start_time = time.time()

        try:
            logger.info(
                f"Generating embedding for query: {request.query[:50]}..."
            )
            query_embedding = await self._generate_query_embedding(
                request.query
            )

            results = await self._search_uploads(
                query_embedding = query_embedding,
                user_id = user_id
                if request.user_id is None else request.user_id,
                limit = request.limit * config.SEARCH_RESULT_MULTIPLIER,
                similarity_threshold = request.similarity_threshold,
            )

            filtered_results = self._apply_filters(results, request)

            final_results = filtered_results[: request.limit]

            search_time_ms = (time.time() - start_time) * 1000

            response = SearchResponse(
                results = final_results,
                total_found = len(filtered_results),
                returned_count = len(final_results),
                search_time_ms = search_time_ms,
                query = request.query,
                query_embedding_generated = True,
                applied_filters = self._get_applied_filters(request),
            )

            logger.info(
                f"Search completed: {len(final_results)} results in {search_time_ms:.1f}ms"
            )
            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            search_time_ms = (time.time() - start_time) * 1000
            return SearchResponse(
                results = [],
                total_found = 0,
                returned_count = 0,
                search_time_ms = search_time_ms,
                query = request.query,
                query_embedding_generated = False,
                applied_filters = None,
            )

    async def _generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding vector for search query

        Args:
            query: Search query text

        Returns:
            1024-dimensional embedding vector
        """
        try:
            cleaned_query = " ".join(query.split())

            # (raw query works better)
            embedding = await local_ai_service.create_embedding_for_query(
                cleaned_query
            )

            if len(embedding
                   ) != config.settings.local_embedding_dimensions:
                raise QueryEmbeddingError(
                    f"Invalid embedding dimensions: {len(embedding)}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Query embedding generation failed: {e}")
            raise QueryEmbeddingError(
                f"Failed to generate embedding: {e!s}"
            ) from e

    async def _search_uploads(
        self,
        query_embedding: list[float],
        user_id: UUID | None,
        limit: int,
        similarity_threshold: float,
    ) -> list[SearchResult]:
        """
        Search uploads using vector similarity

        Args:
            query_embedding: Query embedding vector
            user_id: Optional user filter
            limit: Maximum results
            similarity_threshold: Minimum similarity

        Returns:
            List of search results with similarity scores
        """
        upload_results = await Upload.search_by_embedding(
            query_embedding = query_embedding,
            user_id = user_id,
            limit = limit,
            similarity_threshold = similarity_threshold,
            use_local = True,
        )

        search_results = []
        for rank, (upload, similarity) in enumerate(upload_results, 1):

            distance = 1.0 - similarity

            result = SearchResult(
                upload = upload,
                similarity_score = similarity,
                distance = distance,
                rank = rank,
            )
            search_results.append(result)

        return search_results

    def _apply_filters(
        self,
        results: list[SearchResult],
        request: SearchRequest
    ) -> list[SearchResult]:
        """
        Apply additional filters to search results

        Args:
            results: Initial search results
            request: Search request with filters

        Returns:
            Filtered results
        """
        filtered = results

        if request.file_types:
            filtered = [
                r for r in filtered
                if r.upload.file_type in request.file_types
            ]

        if request.date_from:
            filtered = [
                r for r in filtered
                if r.upload.created_at >= request.date_from
            ]

        if request.date_to:
            filtered = [
                r for r in filtered
                if r.upload.created_at <= request.date_to
            ]

        for rank, result in enumerate(filtered, 1):
            result.rank = rank

        return filtered

    def _get_applied_filters(self,
                             request: SearchRequest) -> dict[str,
                                                             Any] | None:
        """
        Get summary of applied filters

        Args:
            request: Search request

        Returns:
            Dictionary of applied filters or None
        """
        filters: dict[str, Any] = {}

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
        upload: Upload,
        user_id: UUID,
        limit: int = config.SIMILAR_UPLOADS_DEFAULT_LIMIT,
    ) -> list[SearchResult]:
        """
        Find uploads similar to a specific upload.

        Args:
            upload: Upload object (already validated with embedding)
            user_id: Current user ID
            limit: Maximum results

        Returns:
            List of similar uploads ordered by similarity
        """
        if upload.embedding_local is None:
            return []

        results = await self._search_uploads(
            query_embedding = upload.embedding_local,
            user_id = user_id,
            limit = limit + 1,
            similarity_threshold = config.
            SIMILAR_UPLOADS_SIMILARITY_THRESHOLD,
        )

        # Exclude the source upload from results
        filtered_results = [r for r in results if r.upload.id != upload.id]

        return filtered_results[: limit]

    async def batch_search(
        self,
        queries: list[str],
        user_id: UUID | None = None,
        limit: int = config.BATCH_SEARCH_DEFAULT_LIMIT,
        max_concurrent: int = config.BATCH_SEARCH_MAX_CONCURRENT
    ) -> dict[str,
              SearchResponse]:
        """
        Perform multiple searches concurrently.

        Args:
            queries: List of search queries
            user_id: Optional user filter
            limit: Maximum results per query
            max_concurrent: Maximum concurrent searches

        Returns:
            Dictionary mapping queries to results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def search_with_limit(query: str) -> tuple[str,
                                                         SearchResponse]:
            async with semaphore:
                request = SearchRequest(query = query, limit = limit)
                result = await self.search(request, user_id)
                return query, result

        # Execute searches concurrently
        tasks = [search_with_limit(query) for query in queries]
        results = await asyncio.gather(*tasks)

        return dict(results)

    async def get_search_suggestions(  # TODO: make it use search history or popular searches)
        self, partial_query: str, user_id: UUID, limit: int = config.SEARCH_SUGGESTIONS_DEFAULT_LIMIT  # noqa: ARG002
    ) -> list[str]:
        """
        Get search suggestions based on partial query

        Args:
            partial_query: Partial search query
            user_id: User ID
            limit: Maximum suggestions

        Returns:
            List of suggested queries
        """
        # MVP: Return template based suggestions
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

        suggestions = [
            t for t in templates if partial_query.lower() in t.lower()
        ]

        return suggestions[: limit]

    def calculate_embedding_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        similarity = sum(
            a * b for a, b in zip(embedding1, embedding2, strict = False)
        )
        return max(0.0, min(1.0, similarity))


search_service = SearchService()
