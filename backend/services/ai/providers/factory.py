"""
©AngelaMos | 2026
factory.py
"""

import logging
import time

import config
import database
from config import settings

logger = logging.getLogger(__name__)

_cache: dict = {"provider_name": None, "expires_at": 0.0}


def _reset_cache() -> None:
    _cache["provider_name"] = None
    _cache["expires_at"] = 0.0


async def _fetch_provider_from_db() -> str:
    try:
        row = await database.db.fetchrow(
            "SELECT value FROM system_settings WHERE key = 'embedding_provider'"
        )
        if row:
            return str(row["value"])
    except Exception as e:
        logger.warning(f"Failed to fetch provider from DB, using config default: {e}")
    return settings.embedding_provider


async def get_provider():
    """
    Return the active AIProvider instance.
    Reads from system_settings DB with a 5s TTL cache.
    Falls back to config default if DB is unavailable.
    """
    now = time.monotonic()

    if _cache["provider_name"] is not None and now < _cache["expires_at"]:
        provider_name = _cache["provider_name"]
    else:
        provider_name = await _fetch_provider_from_db()
        _cache["provider_name"] = provider_name
        _cache["expires_at"] = now + config.PROVIDER_CACHE_TTL

    if provider_name == "gemini":
        from services.ai.providers.gemini import get_gemini_provider
        return get_gemini_provider()

    from services.ai.providers.local import get_local_provider
    return get_local_provider()


async def set_provider(provider_name: str) -> None:
    """
    Update active provider in DB and invalidate cache.
    provider_name must be 'local' or 'gemini'.
    """
    if provider_name not in ("local", "gemini"):
        raise ValueError(f"Unknown provider: {provider_name}")

    await database.db.execute(
        """
        INSERT INTO system_settings (key, value, updated_at)
        VALUES ('embedding_provider', $1, NOW())
        ON CONFLICT (key) DO UPDATE SET value = $1, updated_at = NOW()
        """,
        provider_name,
    )
    _reset_cache()
    logger.info(f"Provider switched to: {provider_name}")
