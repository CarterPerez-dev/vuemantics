"""
ⒸAngelaMos | 2026
embedding.py
"""

import asyncio
import logging

from starlette import status
import httpx
from ollama import ResponseError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import config
from core import EmbeddingError
from services.ai.manager import OllamaManager


logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Handles embedding generation using bge-m3
    """
    def __init__(
        self,
        ollama: OllamaManager,
        semaphore: asyncio.Semaphore
    ):
        """
        Initialize embedding service

        Args:
            ollama: OllamaManager instance
            semaphore: Semaphore for concurrency control
        """
        self._ollama = ollama
        self._semaphore = semaphore

    @retry(
        retry = retry_if_exception_type(
            (httpx.TimeoutException,
             httpx.ConnectError)
        ),
        stop = stop_after_attempt(3),
        wait = wait_exponential(multiplier = 1,
                                min = 2,
                                max = 30),
    )
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector from text using bge-m3 via Ollama

        Args:
            text: Text to embed (vision description or search query)

        Returns:
            1024-dimensional embedding vector
        """
        try:
            if len(text) > config.MAX_EMBEDDING_TEXT_LENGTH:
                text = text[: config.MAX_EMBEDDING_TEXT_LENGTH] + "..."
                logger.warning(
                    f"Truncated text from {len(text)} to "
                    f"{config.MAX_EMBEDDING_TEXT_LENGTH} chars"
                )

            async with self._semaphore:
                client = await self._ollama.get_client()
                response = await client.embeddings(
                    model = config.settings.local_embedding_model,
                    prompt = text,
                )

                embedding = response["embedding"]

                logger.debug(
                    f"Embedding type: {type(embedding).__name__}, "
                    f"length: {len(embedding)}"
                )

                if len(embedding
                       ) != config.settings.local_embedding_dimensions:
                    raise EmbeddingError(
                        f"Invalid embedding dimensions: {len(embedding)} "
                        f"(expected {config.settings.local_embedding_dimensions})"
                    )

                return embedding  # type: ignore[no-any-return]

        except ResponseError as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                raise EmbeddingError(
                    f"Model not loaded. Run: ollama pull "
                    f"{config.settings.local_embedding_model}"
                ) from e
            raise EmbeddingError(
                f"Embedding model error: {e.error}"
            ) from e
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(
                f"Failed to generate embedding: {e!s}"
            ) from e

    async def create_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for search query.

        Args:
            query: Search query text

        Returns:
            1024-dimensional embedding vector
        """
        return await self.generate_embedding(query)

    async def batch_generate(
        self,
        texts: list[str],
        max_concurrent: int = config.BATCH_EMBEDDING_MAX_CONCURRENT
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            max_concurrent: Max concurrent operations

        Returns:
            List of embedding vectors
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_limit(text: str) -> list[float]:
            async with semaphore:
                return await self.generate_embedding(text)

        tasks = [generate_with_limit(text) for text in texts]
        return await asyncio.gather(*tasks)
