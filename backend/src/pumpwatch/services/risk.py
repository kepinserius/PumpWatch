import logging
from datetime import UTC, datetime
from decimal import Decimal

from pumpwatch.config import settings
from pumpwatch.domain.models import MarketData
from pumpwatch.domain.risk import RiskAssessment, RiskFlag

logger = logging.getLogger(__name__)


class RiskEngine:
    def __init__(self) -> None:
        self.min_liquidity = Decimal(str(settings.min_liquidity_usd))
        self.rules_version = "1.0"

    def assess(self, data: MarketData) -> RiskAssessment:
        flags: list[RiskFlag] = []
        checked_at = datetime.now(UTC)

        flags.append(self._check_liquidity(data, checked_at))
        flags.append(self._check_data_quality(data, checked_at))
        flags.append(self._check_pool_age(data, checked_at))

        failed = [f for f in flags if f.status == "fail"]
        hard_block = any(f.severity == "critical" for f in failed)
        risk_level = "critical" if hard_block else "medium" if failed else "low"

        available = len([f for f in flags if f.status != "unknown"])
        coverage = available / len(flags) if flags else 0.0

        return RiskAssessment(
            token_address=data.token_address,
            chain=data.chain,
            checked_at=checked_at,
            risk_level=risk_level,
            hard_block=hard_block,
            flags=flags,
            coverage=coverage,
            rules_version=self.rules_version,
        )

    def _check_liquidity(self, data: MarketData, checked_at: datetime) -> RiskFlag:
        if data.liquidity_usd is None:
            return RiskFlag(
                name="liquidity_check",
                status="unknown",
                severity="high",
                reason="Liquidity data not available",
                source="market_data",
                checked_at=checked_at,
            )

        if data.liquidity_usd < self.min_liquidity:
            return RiskFlag(
                name="liquidity_check",
                status="fail",
                severity="critical",
                reason=f"Liquidity ${data.liquidity_usd} below minimum ${self.min_liquidity}",
                source="market_data",
                checked_at=checked_at,
            )

        return RiskFlag(
            name="liquidity_check",
            status="pass",
            severity="high",
            reason=f"Liquidity ${data.liquidity_usd} acceptable",
            source="market_data",
            checked_at=checked_at,
        )

    def _check_data_quality(self, data: MarketData, checked_at: datetime) -> RiskFlag:
        if data.data_quality_status == "stale":
            return RiskFlag(
                name="data_quality_check",
                status="fail",
                severity="medium",
                reason="Market data is stale",
                source="validation",
                checked_at=checked_at,
            )

        if data.data_quality_status == "invalid_negative_price":
            return RiskFlag(
                name="data_quality_check",
                status="fail",
                severity="critical",
                reason="Invalid price data",
                source="validation",
                checked_at=checked_at,
            )

        return RiskFlag(
            name="data_quality_check",
            status="pass",
            severity="medium",
            reason="Data quality acceptable",
            source="validation",
            checked_at=checked_at,
        )

    def _check_pool_age(self, data: MarketData, checked_at: datetime) -> RiskFlag:
        return RiskFlag(
            name="pool_age_check",
            status="unknown",
            severity="low",
            reason="Pool age data not available in MVP",
            source="market_data",
            checked_at=checked_at,
        )
