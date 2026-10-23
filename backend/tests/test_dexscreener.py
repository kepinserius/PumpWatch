import pytest

from pumpwatch.domain.models import MarketData
from pumpwatch.providers.dexscreener import DexScreenerAdapter


@pytest.fixture
def mock_pairs_response() -> dict:
    return {
        "pairs": [
            {
                "baseToken": {
                    "address": "So11111111111111111111111111111111111111112",
                    "symbol": "SOL",
                    "name": "Wrapped SOL",
                },
                "pairAddress": "58oQChx4yWmvKFELLZzBi4Fo6CmVE2e6X7DCRwymMgVV",
                "dexId": "raydium",
                "pairCreatedAt": 1700000000000,
                "priceUsd": "150.50",
                "liquidity": {"usd": "1000000.00"},
                "volume": {"m5": "5000", "h1": "50000", "h6": "200000", "h24": "1000000"},
                "priceChange": {"m5": "0.5", "h1": "2.3", "h6": "-1.2", "h24": "5.5"},
                "txns": {
                    "m5": {"buys": 10, "sells": 5},
                    "h1": {"buys": 100, "sells": 80},
                    "h6": {"buys": 500, "sells": 400},
                    "h24": {"buys": 2000, "sells": 1800},
                },
            }
        ]
    }


def test_adapter_creation() -> None:
    adapter = DexScreenerAdapter()
    assert adapter.base_url is not None


@pytest.mark.asyncio
async def test_parse_pair_to_market_data(mock_pairs_response: dict) -> None:
    adapter = DexScreenerAdapter()
    pair = mock_pairs_response["pairs"][0]
    result = adapter._parse_pair_to_market_data(pair, "solana", pair["baseToken"]["address"])

    assert isinstance(result, MarketData)
    assert result.chain == "solana"
    assert result.token_address == "So11111111111111111111111111111111111111112"
    assert result.price_usd is not None
    assert result.liquidity_usd is not None
    assert result.source == "dexscreener"


def test_parse_timestamp_none() -> None:
    adapter = DexScreenerAdapter()
    result = adapter._parse_timestamp(None)
    assert result is None


def test_parse_timestamp_valid() -> None:
    adapter = DexScreenerAdapter()
    result = adapter._parse_timestamp(1700000000000)
    assert result is not None
    assert result.year == 2023
