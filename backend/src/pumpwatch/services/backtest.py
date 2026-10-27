import logging
from datetime import UTC, datetime, timedelta

from pumpwatch.database import Database
from pumpwatch.domain.models import MarketData

logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(self, db: Database):
        self.db = db

    async def run_backtest(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        fee_percent: float = 0.01,
        slippage_percent: float = 0.005,
        strategy: str = "time_based",
        exit_hours: int = 4,
    ) -> int:
        """
        Jalankan backtest untuk periode tertentu.
        Return: run_id dari backtest yang dijalankan.
        """
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        # Insert backtest run
        import json
        
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO backtest_runs 
                (name, strategy_config, fee_percent, slippage_percent, 
                 start_date, end_date, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'running')
                RETURNING id
                """,
                name,
                json.dumps({"strategy": strategy, "exit_hours": exit_hours}),
                fee_percent,
                slippage_percent,
                start_date,
                end_date,
            )
            run_id = row["id"]

        # Ambil signals dalam periode
        signals = await self._get_signals_in_range(start_date, end_date)

        for signal in signals:
            try:
                await self._simulate_signal(
                    run_id, signal, strategy, exit_hours, fee_percent, slippage_percent
                )
            except Exception as e:
                logger.error(f"Error simulating signal {signal['id']}: {e}")
                continue

        # Update status completed
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE backtest_runs SET status = 'completed' WHERE id = $1",
                run_id,
            )

        return run_id

    async def _get_signals_in_range(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        """Ambil signals dalam periode."""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT s.*, t.id as token_id, t.chain, t.address
                FROM signals s
                JOIN tokens t ON t.id = s.token_id
                WHERE s.created_at >= $1 AND s.created_at <= $2
                ORDER BY s.created_at ASC
                """,
                start,
                end,
            )
            return [dict(row) for row in rows]

    async def _simulate_signal(
        self,
        run_id: int,
        signal: dict,
        strategy: str,
        exit_hours: int,
        fee_percent: float,
        slippage_percent: float,
    ) -> None:
        """Simulate single signal entry + exit."""
        token_id = signal["token_id"]
        entry_price = float(signal["entry_price_usd"]) if signal["entry_price_usd"] else None

        if not entry_price:
            logger.debug(f"Skipping signal {signal['id']}: no entry price")
            return

        entry_timestamp = signal["created_at"]
        exit_timestamp = entry_timestamp + timedelta(hours=exit_hours)

        # Ambil harga exit
        exit_price = await self._get_price_at(token_id, exit_timestamp)

        if not exit_price:
            # Fallback: gunakan harga terdekat setelah entry
            exit_price = await self._get_latest_price_after(token_id, entry_timestamp)

        if not exit_price:
            logger.debug(f"No exit price found for signal {signal['id']}")
            return

        # Hitung PnL
        position_size = 1000.0  # Fixed untuk simplicity
        gross_return = (exit_price - entry_price) / entry_price * position_size
        fees = position_size * (fee_percent * 2)  # Entry + exit fees
        slippage_impact = position_size * slippage_percent * 2
        net_return = gross_return - fees - slippage_impact

        # Insert trade
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO backtest_trades 
                (backtest_run_id, signal_id, token_id, entry_timestamp, 
                 entry_price, exit_timestamp, exit_price, position_size_usd,
                 gross_return, net_return, fees_paid, slippage_impact, exit_reason)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                run_id,
                signal["id"],
                token_id,
                entry_timestamp,
                entry_price,
                exit_timestamp,
                exit_price,
                position_size,
                gross_return,
                net_return,
                fees,
                slippage_impact,
                f"time_{exit_hours}h",
            )

    async def _get_price_at(self, token_id: int, timestamp: datetime) -> float | None:
        """Get price pada timestamp tertentu."""
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT price_usd FROM market_snapshots
                WHERE token_id = $1 AND observed_at <= $2
                ORDER BY observed_at DESC
                LIMIT 1
                """,
                token_id,
                timestamp,
            )
            return float(row["price_usd"]) if row and row["price_usd"] else None

    async def _get_latest_price_after(
        self, token_id: int, after: datetime
    ) -> float | None:
        """Get latest price setelah timestamp."""
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT price_usd FROM market_snapshots
                WHERE token_id = $1 AND observed_at > $2
                ORDER BY observed_at ASC
                LIMIT 1
                """,
                token_id,
                after,
            )
            return float(row["price_usd"]) if row and row["price_usd"] else None

    async def get_backtest_results(self, run_id: int) -> dict:
        """Get backtest results + metrics."""
        async with self.db.pool.acquire() as conn:
            run = await conn.fetchrow(
                "SELECT * FROM backtest_runs WHERE id = $1",
                run_id,
            )
            if not run:
                raise ValueError(f"Backtest run {run_id} not found")

            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_trades,
                    AVG(net_return) as avg_return,
                    SUM(CASE WHEN net_return > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN net_return <= 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(fees_paid) as total_fees,
                    SUM(slippage_impact) as total_slippage,
                    MAX(net_return) as max_return,
                    MIN(net_return) as min_return
                FROM backtest_trades
                WHERE backtest_run_id = $1
                """,
                run_id,
            )

            trades = await conn.fetch(
                """
                SELECT * FROM backtest_trades
                WHERE backtest_run_id = $1
                ORDER BY entry_timestamp ASC
                LIMIT 100
                """,
                run_id,
            )

            equity = await self._calculate_equity_curve(run_id)

            return {
                "run": dict(run),
                "stats": {
                    "total_trades": stats["total_trades"] or 0,
                    "winning_trades": stats["winning_trades"] or 0,
                    "losing_trades": stats["losing_trades"] or 0,
                    "win_rate": (stats["winning_trades"] / stats["total_trades"] * 100) if stats["total_trades"] else 0,
                    "avg_return": float(stats["avg_return"]) if stats["avg_return"] else 0.0,
                    "total_fees": float(stats["total_fees"]) if stats["total_fees"] else 0.0,
                    "total_slippage": float(stats["total_slippage"]) if stats["total_slippage"] else 0.0,
                    "max_return": float(stats["max_return"]) if stats["max_return"] else 0.0,
                    "min_return": float(stats["min_return"]) if stats["min_return"] else 0.0,
                },
                "equity_curve": equity,
                "trades": [dict(t) for t in trades],
            }

    async def _calculate_equity_curve(self, run_id: int) -> list[dict]:
        """Calculate equity curve dari trades."""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT entry_timestamp, net_return
                FROM backtest_trades
                WHERE backtest_run_id = $1
                ORDER BY entry_timestamp ASC
                """,
                run_id,
            )

        equity = 10000.0  # Starting capital
        curve = []
        cumulative = 0.0

        for row in rows:
            cumulative += float(row["net_return"]) if row["net_return"] else 0.0
            equity = 10000 + cumulative
            curve.append({
                "timestamp": row["entry_timestamp"].isoformat(),
                "equity": round(equity, 2),
                "return": round(cumulative, 2),
            })

        return curve

    async def list_backtest_runs(self, limit: int = 20, offset: int = 0) -> list[dict]:
        """List backtest runs."""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM backtest_runs
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [dict(row) for row in rows]

    async def get_backtest_trades(
        self, run_id: int, limit: int = 50
    ) -> list[dict]:
        """List trades dari backtest tertentu."""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM backtest_trades
                WHERE backtest_run_id = $1
                ORDER BY entry_timestamp DESC
                LIMIT $2
                """,
                run_id,
                limit,
            )
            return [dict(t) for t in rows]
