"""
©AngelaMos | 2026
local.py
"""

import logging

from models.Upload import Upload
from services.ai.service import local_ai_service

logger = logging.getLogger(__name__)


class LocalProvider:
    """
    AIProvider implementation using local Ollama models (Qwen + bge-m3).
    Delegates all processing to the existing LocalAIService.
    """
    provider_name = "local"

    async def process_upload(self, upload: Upload) -> None:
        await local_ai_service.analyze_media(upload.id)

    async def generate_query_embedding(self, query: str) -> list[float]:
        return await local_ai_service.create_embedding_for_query(query)


_instance: LocalProvider | None = None


def get_local_provider() -> LocalProvider:
    global _instance
    if _instance is None:
        _instance = LocalProvider()
    return _instance
