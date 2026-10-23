import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone

from pumpwatch.domain.models import MarketData
from pumpwatch.domain.risk import RiskAssessment, RiskFlag
from pumpwatch.domain.scoring import MomentumScore, ScoreComponent
from pumpwatch.services.alerts import TelegramAlert


@pytest.fixture
def mock_score():
    return MomentumScore(
        token_address="So11111111111111111111111111111111111111112",
        chain="solana",
        calculated_at=datetime.now(timezone.utc),
        total_score=75,
        components=[
            ScoreComponent("volume_growth", 0.8, 0.25, {"available": True}),
            ScoreComponent("buy_pressure", 0.7, 0.20, {"available": True}),
        ],
        features={},
        data_coverage=0.8,
    )


@pytest.fixture
def mock_risk():
    return RiskAssessment(
        token_address="So11111111111111111111111111111111111111112",
        chain="solana",
        checked_at=datetime.now(timezone.utc),
        risk_level="low",
        hard_block=False,
        flags=[
            RiskFlag(
                name="liquidity_check",
                status="pass",
                severity="high",
                reason="Liquidity acceptable",
                source="market_data",
                checked_at=datetime.now(timezone.utc),
            )
        ],
        coverage=1.0,
    )


class TestTelegramAlert:
    def test_format_message(self, mock_score, mock_risk):
        alert = TelegramAlert()
        message = alert._format_message("So11111111111111111111111111111111111111112", "solana", mock_score, mock_risk)
        
        assert "PumpWatch Alert" in message
        assert "So11111111111111" in message
        assert "75/100" in message
        assert "SOLANA" in message.upper()

    def test_get_category(self):
        alert = TelegramAlert()
        
        assert "Momentum tinggi" in alert._get_category(85)
        assert "Watchlist" in alert._get_category(70)
        assert "Belum memenuhi threshold" in alert._get_category(50)

    @pytest.mark.asyncio
    async def test_send_alert_without_config(self, mock_score, mock_risk):
        alert = TelegramAlert()
        alert.bot_token = ""
        alert.chat_id = ""
        
        result = await alert.send_alert("test_address", "solana", mock_score, mock_risk)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_with_hard_block(self, mock_score, mock_risk):
        alert = TelegramAlert()
        alert.bot_token = "test_token"
        alert.chat_id = "test_chat"
        mock_risk.hard_block = True
        
        result = await alert.send_alert("test_address", "solana", mock_score, mock_risk)
        
        assert result is False
