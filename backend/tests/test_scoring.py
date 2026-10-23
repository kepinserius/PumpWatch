from datetime import UTC, datetime
from decimal import Decimal

import pytest

from pumpwatch.domain.models import MarketData
from pumpwatch.services.risk import RiskEngine
from pumpwatch.services.scoring import MomentumEngine


@pytest.fixture
def sample_market_data() -> MarketData:
    return MarketData(
        chain="solana",
        token_address="So11111111111111111111111111111111111111112",
        pool_address="58oQChx4yWmvKFELLZzBi4Fo6CmVE2e6X7DCRwymMgVV",
        observed_at=datetime.now(UTC),
        source="dexscreener",
        price_usd=Decimal("150.50"),
        liquidity_usd=Decimal("1000000.00"),
        volume_5m=Decimal("5000"),
        volume_1h=Decimal("50000"),
        volume_6h=Decimal("200000"),
        volume_24h=Decimal("1000000"),
        price_change_5m=Decimal("0.5"),
        price_change_1h=Decimal("2.3"),
        price_change_6h=Decimal("-1.2"),
        price_change_24h=Decimal("5.5"),
        buys_5m=10,
        buys_1h=100,
        buys_6h=500,
        buys_24h=2000,
        sells_5m=5,
        sells_1h=80,
        sells_6h=400,
        sells_24h=1800,
    )


class TestRiskEngine:
    def test_assess_passes_with_good_liquidity(self, sample_market_data: MarketData) -> None:
        engine = RiskEngine()
        result = engine.assess(sample_market_data)

        assert result.risk_level in ("low", "medium")
        assert result.hard_block is False
        assert result.coverage > 0

    def test_assess_fails_with_low_liquidity(self, sample_market_data: MarketData) -> None:
        sample_market_data.liquidity_usd = Decimal("100.00")
        engine = RiskEngine()
        result = engine.assess(sample_market_data)

        assert result.hard_block is True
        assert result.risk_level == "critical"

    def test_assess_unknown_without_liquidity(self, sample_market_data: MarketData) -> None:
        sample_market_data.liquidity_usd = None
        engine = RiskEngine()
        result = engine.assess(sample_market_data)

        liquidity_flag = next((f for f in result.flags if f.name == "liquidity_check"), None)
        assert liquidity_flag is not None
        assert liquidity_flag.status == "unknown"


class TestMomentumEngine:
    def test_calculate_returns_score(self, sample_market_data: MarketData) -> None:
        engine = MomentumEngine()
        result = engine.calculate(sample_market_data)

        assert 0 <= result.total_score <= 100
        assert result.data_coverage > 0
        assert len(result.components) == 6

    def test_calculate_handles_missing_data(self, sample_market_data: MarketData) -> None:
        sample_market_data.volume_1h = None
        sample_market_data.volume_24h = None
        engine = MomentumEngine()
        result = engine.calculate(sample_market_data)

        assert result.total_score >= 0

    def test_volume_growth_score(self, sample_market_data: MarketData) -> None:
        sample_market_data.volume_1h = Decimal("100000")
        engine = MomentumEngine()
        result = engine.calculate(sample_market_data)

        vol_component = next((c for c in result.components if c.name == "volume_growth"), None)
        assert vol_component is not None
        assert vol_component.score > 0.5

    def test_buy_pressure_score(self, sample_market_data: MarketData) -> None:
        sample_market_data.buys_1h = 200
        sample_market_data.sells_1h = 50
        engine = MomentumEngine()
        result = engine.calculate(sample_market_data)

        pressure = next((c for c in result.components if c.name == "buy_pressure"), None)
        assert pressure is not None
        assert pressure.score > 0.7
