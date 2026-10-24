import logging
from datetime import UTC, datetime, timedelta

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

        cutoff = datetime.now(UTC) - timedelta(minutes=self.cooldown_minutes)
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

    async def _record_signal(self, data: MarketData, score: MomentumScore, risk: RiskAssessment) -> int | None:
        token_id = await self.db.get_token_id(data.chain, data.token_address)
        if not token_id:
            return None

        pool_id = None
        if data.pool_address:
            pool_id = await self.db.get_pool_id(data.chain, data.pool_address)

        entry_price = float(data.price_usd) if data.price_usd else None
        signal_id = await self.db.insert_signal(token_id, pool_id, score, risk, entry_price)
        return signal_id

    async def _update_cooldown(self, chain: str, address: str) -> None:
        token_id = await self.db.get_token_id(chain, address)
        if not token_id:
            return

        signal_id = await self._get_latest_signal_id(token_id)
        if signal_id:
            dedupe_key = f"{chain}:{address}:{datetime.now(timezone.utc).date()}"
            await self.db.insert_alert(signal_id, "telegram", dedupe_key)

    async def _get_latest_signal_id(self, token_id: int) -> int | None:
        if not self.db.pool:
            return None
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM signals WHERE token_id = $1 ORDER BY created_at DESC LIMIT 1",
                token_id,
            )
            return row["id"] if row else None
