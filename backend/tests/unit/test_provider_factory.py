"""
©AngelaMos | 2026
test_provider_factory.py
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_factory_returns_local_by_default():
    with patch(
        "services.ai.providers.factory._fetch_provider_from_db", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = "local"
        from services.ai.providers.factory import get_provider, _reset_cache
        _reset_cache()
        provider = await get_provider()
        assert provider.provider_name == "local"


@pytest.mark.asyncio
async def test_factory_uses_cache():
    call_count = 0

    async def counting_fetch():
        nonlocal call_count
        call_count += 1
        return "local"

    with patch(
        "services.ai.providers.factory._fetch_provider_from_db",
        side_effect=counting_fetch,
    ):
        from services.ai.providers.factory import get_provider, _reset_cache
        _reset_cache()
        await get_provider()
        await get_provider()
        assert call_count == 1


@pytest.mark.asyncio
async def test_factory_reset_cache_forces_refetch():
    call_count = 0

    async def counting_fetch():
        nonlocal call_count
        call_count += 1
        return "local"

    with patch(
        "services.ai.providers.factory._fetch_provider_from_db",
        side_effect=counting_fetch,
    ):
        from services.ai.providers.factory import get_provider, _reset_cache
        _reset_cache()
        await get_provider()
        _reset_cache()
        await get_provider()
        assert call_count == 2
