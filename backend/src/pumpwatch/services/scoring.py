import logging
from datetime import UTC, datetime

from pumpwatch.domain.models import MarketData
from pumpwatch.domain.scoring import MomentumScore, ScoreComponent

logger = logging.getLogger(__name__)


class MomentumEngine:
    def __init__(self) -> None:
        self.rules_version = "1.0"
        self.weights = {
            "volume_growth": 0.25,
            "buy_pressure": 0.20,
            "liquidity_quality": 0.20,
            "activity_growth": 0.15,
            "price_momentum": 0.10,
            "pool_quality": 0.10,
        }

    def calculate(self, data: MarketData) -> MomentumScore:
        components = [
            self._calc_volume_growth(data),
            self._calc_buy_pressure(data),
            self._calc_liquidity_quality(data),
            self._calc_activity_growth(data),
            self._calc_price_momentum(data),
            self._calc_pool_quality(data),
        ]

        available = [c for c in components if c.details.get("available", False)]
        if not available:
            return self._insufficient_data_score(data)

        total_weight = sum(c.weight for c in available)
        weighted_sum = sum(c.score * c.weight for c in available)
        raw_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        coverage = len(available) / len(components)
        normalized_score = min(100, max(0, raw_score * 100))

        return MomentumScore(
            token_address=data.token_address,
            chain=data.chain,
            calculated_at=datetime.now(UTC),
            total_score=int(normalized_score),
            components=components,
            features=self._extract_features(data),
            data_coverage=coverage,
            rules_version=self.rules_version,
        )

    def _calc_volume_growth(self, data: MarketData) -> ScoreComponent:
        if data.volume_1h is None or data.volume_24h is None:
            return ScoreComponent(
                name="volume_growth",
                score=0.0,
                weight=self.weights["volume_growth"],
                details={"available": False, "reason": "Volume data missing"},
            )

        if data.volume_24h == 0:
            return ScoreComponent(
                name="volume_growth",
                score=0.0,
                weight=self.weights["volume_growth"],
                details={"available": True, "reason": "Zero 24h volume"},
            )

        hourly_avg = data.volume_24h / 24
        ratio = float(data.volume_1h / hourly_avg) if hourly_avg > 0 else 0.0
        score = min(1.0, ratio / 3.0)

        return ScoreComponent(
            name="volume_growth",
            score=score,
            weight=self.weights["volume_growth"],
            details={
                "available": True,
                "volume_1h": float(data.volume_1h),
                "volume_24h": float(data.volume_24h),
                "ratio": ratio,
            },
        )

    def _calc_buy_pressure(self, data: MarketData) -> ScoreComponent:
        if data.buys_1h is None or data.sells_1h is None:
            return ScoreComponent(
                name="buy_pressure",
                score=0.0,
                weight=self.weights["buy_pressure"],
                details={"available": False, "reason": "Buy/sell data missing"},
            )

        total = data.buys_1h + data.sells_1h
        if total == 0:
            return ScoreComponent(
                name="buy_pressure",
                score=0.5,
                weight=self.weights["buy_pressure"],
                details={"available": True, "reason": "No transactions"},
            )

        ratio = data.buys_1h / total
        score = ratio

        return ScoreComponent(
            name="buy_pressure",
            score=score,
            weight=self.weights["buy_pressure"],
            details={
                "available": True,
                "buys_1h": data.buys_1h,
                "sells_1h": data.sells_1h,
                "ratio": ratio,
            },
        )

    def _calc_liquidity_quality(self, data: MarketData) -> ScoreComponent:
        if data.liquidity_usd is None:
            return ScoreComponent(
                name="liquidity_quality",
                score=0.0,
                weight=self.weights["liquidity_quality"],
                details={"available": False, "reason": "Liquidity data missing"},
            )

        liq = float(data.liquidity_usd)
        if liq >= 100_000:
            score = 1.0
        elif liq >= 50_000:
            score = 0.8
        elif liq >= 10_000:
            score = 0.6
        elif liq >= 5_000:
            score = 0.4
        else:
            score = 0.2

        return ScoreComponent(
            name="liquidity_quality",
            score=score,
            weight=self.weights["liquidity_quality"],
            details={"available": True, "liquidity_usd": liq},
        )

    def _calc_activity_growth(self, data: MarketData) -> ScoreComponent:
        if data.buys_1h is None or data.buys_24h is None:
            return ScoreComponent(
                name="activity_growth",
                score=0.0,
                weight=self.weights["activity_growth"],
                details={"available": False, "reason": "Activity data missing"},
            )

        if data.buys_24h == 0:
            return ScoreComponent(
                name="activity_growth",
                score=0.0,
                weight=self.weights["activity_growth"],
                details={"available": True, "reason": "Zero activity"},
            )

        hourly_avg = data.buys_24h / 24
        ratio = data.buys_1h / hourly_avg if hourly_avg > 0 else 0.0
        score = min(1.0, ratio / 3.0)

        return ScoreComponent(
            name="activity_growth",
            score=score,
            weight=self.weights["activity_growth"],
            details={
                "available": True,
                "buys_1h": data.buys_1h,
                "buys_24h": data.buys_24h,
                "ratio": ratio,
            },
        )

    def _calc_price_momentum(self, data: MarketData) -> ScoreComponent:
        if data.price_change_1h is None:
            return ScoreComponent(
                name="price_momentum",
                score=0.0,
                weight=self.weights["price_momentum"],
                details={"available": False, "reason": "Price change data missing"},
            )

        change = float(data.price_change_1h)
        if change >= 50:
            score = 1.0
        elif change >= 20:
            score = 0.8
        elif change >= 10:
            score = 0.6
        elif change >= 0:
            score = 0.4
        elif change >= -10:
            score = 0.3
        else:
            score = 0.1

        return ScoreComponent(
            name="price_momentum",
            score=score,
            weight=self.weights["price_momentum"],
            details={"available": True, "price_change_1h": change},
        )

    def _calc_pool_quality(self, data: MarketData) -> ScoreComponent:
        return ScoreComponent(
            name="pool_quality",
            score=0.5,
            weight=self.weights["pool_quality"],
            details={"available": False, "reason": "Pool age data not available in MVP"},
        )

    def _insufficient_data_score(self, data: MarketData) -> MomentumScore:
        return MomentumScore(
            token_address=data.token_address,
            chain=data.chain,
            calculated_at=datetime.now(UTC),
            total_score=0,
            components=[],
            features={},
            data_coverage=0.0,
            rules_version=self.rules_version,
        )

    def _extract_features(self, data: MarketData) -> dict[str, float | int | None]:
        return {
            "price_usd": float(data.price_usd) if data.price_usd else None,
            "liquidity_usd": float(data.liquidity_usd) if data.liquidity_usd else None,
            "volume_1h": float(data.volume_1h) if data.volume_1h else None,
            "volume_24h": float(data.volume_24h) if data.volume_24h else None,
            "buys_1h": data.buys_1h,
            "sells_1h": data.sells_1h,
            "price_change_1h": float(data.price_change_1h) if data.price_change_1h else None,
        }
