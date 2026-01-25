"""
ⒸAngelaMos | 2026
manager.py
"""


import httpx
from ollama import AsyncClient

import config


class OllamaManager:
    """
    Manages Ollama client connection
    """
    def __init__(self) -> None:
        """
        Initialize Ollama manager
        """
        self._ollama_client: AsyncClient | None = None

    async def get_client(self) -> AsyncClient:
        """
        Get or create Ollama async client
        """
        if self._ollama_client is None:
            self._ollama_client = AsyncClient(
                host = config.settings.ollama_host,
                timeout = httpx.Timeout(
                    connect = 10.0,
                    read = 300.0,
                    write = 60.0,
                    pool = 30.0
                ),
            )
        return self._ollama_client

    async def list_models(self) -> list[str]:
        """
        List available models in Ollama
        """
        client = await self.get_client()
        models = await client.list()
        return [m["name"] for m in models.get("models", [])]

    async def check_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available
        """
        models = await self.list_models()
        base_name = model_name.split(":")[0]
        return any(base_name in m for m in models)
