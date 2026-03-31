"""
©AngelaMos | 2026
AI provider implementations
"""

from services.ai.providers.base import AIProvider, ProcessResult
from services.ai.providers.local import LocalProvider, get_local_provider
from services.ai.providers.gemini import GeminiProvider, get_gemini_provider
from services.ai.providers.factory import get_provider, set_provider

__all__ = [
    "AIProvider",
    "ProcessResult",
    "LocalProvider",
    "get_local_provider",
    "GeminiProvider",
    "get_gemini_provider",
    "get_provider",
    "set_provider",
]
