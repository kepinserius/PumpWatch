import logging
from datetime import datetime, timedelta, timezone

from pumpwatch.config import settings
from pumpwatch.database import Database
from pumpwatch.domain.models import MarketData
from pumpwatch.services.alerts import TelegramAlert
from pumpwatch.services.risk import RiskEngine
from pumpwatch.services.scoring import MomentumEngine

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, db: Database, telegram: TelegramAlert) -> None:
        self.db = db
        self.telegram = telegram
        self.risk_engine = RiskEngine()
        self.scoring_engine = MomentumEngine()
        self.threshold = settings.momentum_threshold
        self.cooldown_minutes = settings.alert_cooldown_minutes

    async def evaluate_and_alert(self, data: MarketData) -> bool:
        if await self._is_in_cooldown(data.chain, data.token_address):
            logger.debug(f"Token {data.token_address} in cooldown, skipping")
            return False

        risk = self.risk_engine.assess(data)
        if risk.hard_block:
            logger.info(f"Token {data.token_address} hard-blocked by risk")
            return False

        score = self.scoring_engine.calculate(data)
        if score.total_score < self.threshold:
            logger.debug(f"Token {data.token_address} score {score.total_score} below threshold")
            return False

        await self._record_signal(data, score, risk)

        sent = await self.telegram.send_alert(data.token_address, data.chain, score, risk)
        if sent:
            await self._update_cooldown(data.chain, data.token_address)

        return sent

    async def _is_in_cooldown(self, chain: str, address: str) -> bool:
        if not self.db.pool:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.cooldown_minutes)
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 1 FROM alerts a
                JOIN signals s ON a.signal_id = s.id
                JOIN tokens t ON s.token_id = t.id
                WHERE t.chain = $1 AND t.address = $2
                AND a.sent_at > $3
                LIMIT 1
                """,
                chain,
                address,
                cutoff,
            )
            return row is not None

    async def _record_signal(self, data: MarketData, score: any, risk: any) -> None:
        pass

    async def _update_cooldown(self, chain: str, address: str) -> None:
        pass
