import logging
from datetime import UTC, datetime
from decimal import Decimal

from pumpwatch.database import Database

logger = logging.getLogger(__name__)


class PaperTrader:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.position_size = Decimal("100.00")
        self.fee = Decimal("0.01")
        self.slippage = Decimal("0.02")

    async def open_position(self, signal_id: int, entry_price: Decimal) -> int | None:
        if not self.db.pool:
            return None

        slippage_adjusted = entry_price * (1 + self.slippage)
        net_entry = slippage_adjusted * (1 + self.fee)

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO paper_trades (
                    signal_id, entry_timestamp, reference_entry_price,
                    simulated_entry_price, position_size_usd,
                    fee_assumption, slippage_assumption, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'open')
                RETURNING id
                """,
                signal_id,
                datetime.now(UTC),
                entry_price,
                net_entry,
                self.position_size,
                self.fee,
                self.slippage,
            )
            logger.info(f"Opened paper trade {row['id']} for signal {signal_id}")
            return row["id"] if row else None

    async def close_position(self, trade_id: int, exit_price: Decimal) -> Decimal | None:
        if not self.db.pool:
            return None

        async with self.db.pool.acquire() as conn:
            trade = await conn.fetchrow(
                "SELECT * FROM paper_trades WHERE id = $1 AND status = 'open'",
                trade_id,
            )
            if not trade:
                return None

            entry = Decimal(str(trade["simulated_entry_price"]))
            slippage_adjusted_exit = exit_price * (1 - self.slippage)
            net_exit = slippage_adjusted_exit * (1 - self.fee)

            net_return = (net_exit - entry) / entry if entry > 0 else Decimal("0")

            await conn.execute(
                """
                UPDATE paper_trades
                SET exit_timestamp = $2, simulated_exit_price = $3,
                    net_return = $4, status = 'closed'
                WHERE id = $1
                """,
                trade_id,
                datetime.now(UTC),
                net_exit,
                net_return,
            )

            logger.info(f"Closed paper trade {trade_id} with return {float(net_return) * 100:.2f}%")
            return net_return

    async def get_open_positions(self) -> list[dict]:
        if not self.db.pool:
            return []

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT pt.*, t.chain, t.address, t.symbol
                FROM paper_trades pt
                JOIN signals s ON pt.signal_id = s.id
                JOIN tokens t ON s.token_id = t.id
                WHERE pt.status = 'open'
                ORDER BY pt.entry_timestamp DESC
                """
            )
            return [dict(row) for row in rows]

    async def get_trade_history(self, limit: int = 100) -> list[dict]:
        if not self.db.pool:
            return []

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT pt.*, t.chain, t.address, t.symbol
                FROM paper_trades pt
                JOIN signals s ON pt.signal_id = s.id
                JOIN tokens t ON s.token_id = t.id
                ORDER BY pt.entry_timestamp DESC
                LIMIT $1
                """,
                limit,
            )
            return [dict(row) for row in rows]
