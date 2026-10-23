
import pytest

from pumpwatch.domain.models import MarketData
from pumpwatch.providers.dexscreener import DexScreenerAdapter


@pytest.fixture
def adapter():
    return DexScreenerAdapter()


@pytest.mark.asyncio
async def test_fetch_new_pairs_real(adapter):
    pairs = await adapter.fetch_new_pairs("solana", limit=5)
    assert isinstance(pairs, list)


@pytest.mark.asyncio
async def test_fetch_market_data_real(adapter):
    data = await adapter.fetch_market_data("solana", "So11111111111111111111111111111111111111112")
    assert data is None or isinstance(data, MarketData)


@pytest.mark.asyncio
async def test_health_check(adapter):
    is_healthy, message = await adapter.health_check()
    assert isinstance(is_healthy, bool)
    assert isinstance(message, str)
