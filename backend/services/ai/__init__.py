"""
ⒸAngelaMos | 2026
AI services package for local model inference
"""

from services.ai.embedding import EmbeddingService
from services.ai.manager import OllamaManager
from services.ai.service import LocalAIService, local_ai_service
from services.ai.vision import VisionService
from services.ai.regenerate import regenerate_upload_description


__all__ = [
    "OllamaManager",
    "VisionService",
    "EmbeddingService",
    "LocalAIService",
    "local_ai_service",
    "regenerate_upload_description",
]
