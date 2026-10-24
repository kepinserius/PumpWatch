import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from pumpwatch.database import Database
from pumpwatch.providers.dexscreener import DexScreenerAdapter

logger = logging.getLogger(__name__)


class OutcomeTracker:
    def __init__(self, db: Database, provider: DexScreenerAdapter) -> None:
        self.db = db
        self.provider = provider
        self.horizons = [
            ("5m", timedelta(minutes=5)),
            ("15m", timedelta(minutes=15)),
            ("1h", timedelta(hours=1)),
            ("4h", timedelta(hours=4)),
            ("24h", timedelta(hours=24)),
        ]
        self.fee_assumption = Decimal("0.01")
        self.slippage_assumption = Decimal("0.02")

    async def track_outcomes(self) -> int:
        if not self.db.pool:
            return 0

        tracked = 0
        for horizon_name, horizon_delta in self.horizons:
            signals = await self._get_pending_signals(horizon_name, horizon_delta)
            for signal in signals:
                try:
                    await self._record_outcome(signal, horizon_name, horizon_delta)
                    tracked += 1
                except Exception as e:
                    logger.error(f"Failed to track outcome for signal {signal['id']}: {e}")

        return tracked

    async def _get_pending_signals(self, horizon: str, delta: timedelta) -> list[dict]:
        if not self.db.pool:
            return []

        cutoff = datetime.now(UTC) - delta
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT s.id, s.token_id, s.created_at, s.entry_price_usd,
                       t.chain, t.address
                FROM signals s
                JOIN tokens t ON s.token_id = t.id
                WHERE s.created_at <= $1
                AND s.entry_price_usd IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM signal_outcomes o
                    WHERE o.signal_id = s.id AND o.price_{horizon} IS NOT NULL
                )
                """,
                cutoff,
            )
            return [dict(row) for row in rows]

    async def _record_outcome(self, signal: dict, horizon: str, delta: timedelta) -> None:
        market_data = await self.provider.fetch_market_data(signal["chain"], signal["address"])
        if not market_data or not market_data.price_usd:
            logger.warning(f"No price data for signal {signal['id']}")
            return

        current_price = market_data.price_usd
        entry_price = Decimal(str(signal["entry_price_usd"]))

        price_column = f"price_{horizon}"
        return_column = f"return_{horizon}"
        return_net_column = f"return_net_{horizon}"

        price_change = (current_price - entry_price) / entry_price if entry_price > 0 else Decimal("0")
        net_return = price_change - self.fee_assumption - self.slippage_assumption

        if not self.db.pool:
            return

        async with self.db.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM signal_outcomes WHERE signal_id = $1",
                signal["id"],
            )

            if existing:
                await conn.execute(
                    f"""
                    UPDATE signal_outcomes
                    SET {price_column} = $2, {return_column} = $3, {return_net_column} = $4,
                        checked_at = NOW(), liquidity_available = $5
                    WHERE signal_id = $1
                    """,
                    signal["id"],
                    current_price,
                    price_change,
                    net_return,
                    market_data.liquidity_usd is not None and market_data.liquidity_usd > 0,
                )
            else:
                await conn.execute(
                    f"""
                    INSERT INTO signal_outcomes (
                        signal_id, checked_at, {price_column}, {return_column}, {return_net_column},
                        liquidity_available, data_available
                    ) VALUES ($1, NOW(), $2, $3, $4, $5, true)
                    """,
                    signal["id"],
                    current_price,
                    price_change,
                    net_return,
                    market_data.liquidity_usd is not None and market_data.liquidity_usd > 0,
                )

        await self._update_mfe_mae(signal["id"], entry_price, current_price)

    async def _update_mfe_mae(self, signal_id: int, entry_price: Decimal, current_price: Decimal) -> None:
        if not self.db.pool:
            return

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT mfe, mae FROM signal_outcomes WHERE signal_id = $1",
                signal_id,
            )

            if not row:
                return

            current_return = (current_price - entry_price) / entry_price if entry_price > 0 else Decimal("0")

            mfe = row["mfe"] or Decimal("0")
            mae = row["mae"] or Decimal("0")

            if current_return > mfe:
                mfe = current_return
            if current_return < mae:
                mae = current_return

            await conn.execute(
                "UPDATE signal_outcomes SET mfe = $2, mae = $3 WHERE signal_id = $1",
                signal_id,
                mfe,
                mae,
            )
