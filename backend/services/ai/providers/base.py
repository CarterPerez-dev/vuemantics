"""
©AngelaMos | 2026
base.py
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from models.Upload import Upload


@dataclass
class ProcessResult:
    embedding: list[float]
    description: str | None


@runtime_checkable
class AIProvider(Protocol):
    provider_name: str

    async def process_upload(self, upload: Upload) -> None:
        """
        Process upload: embed (and describe if local), write to DB, publish WebSocket progress.
        Raises on unrecoverable error; caller handles retry logic.
        """
        ...

    async def generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for a search query text.
        """
        ...
