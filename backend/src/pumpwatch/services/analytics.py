import logging
from datetime import UTC, datetime, timedelta

from pumpwatch.database import Database

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: Database):
        self.db = db

    async def compute_aggregates(self, timeframe: str = '1h') -> None:
        """
        Hitung agregat momentum/risk untuk window terakhir.
        Timeframe: 1h, 4h, 24h
        """
        if not self.db.pool:
            logger.warning("Database pool not available")
            return

        now = datetime.now(UTC)
        time_bucket = self._get_time_bucket(now, timeframe)

        momentum_agg = await self._compute_momentum_aggregate(time_bucket, timeframe)
        risk_agg = await self._compute_risk_aggregate(time_bucket, timeframe)

        await self._insert_momentum_aggregate(momentum_agg)
        await self._insert_risk_aggregate(risk_agg)

        logger.info(f"Computed aggregates for {timeframe} at {time_bucket.isoformat()}")

    def _get_time_bucket(self, dt: datetime, timeframe: str) -> datetime:
        """Round datetime to timeframe bucket."""
        if timeframe == '1h':
            return dt.replace(minute=0, second=0, microsecond=0)
        elif timeframe == '4h':
            hour = (dt.hour // 4) * 4
            return dt.replace(hour=hour, minute=0, second=0, microsecond=0)
        elif timeframe == '24h':
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return dt

    async def _compute_momentum_aggregate(self, time_bucket: datetime, timeframe: str) -> dict:
        """Compute momentum aggregate dari momentum_snapshots."""
        window_start = time_bucket - self._get_window_delta(timeframe)

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    AVG(momentum_score) as avg_score,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY momentum_score) as median_score,
                    COUNT(CASE WHEN momentum_score >= 80 THEN 1 END) as high_count,
                    COUNT(CASE WHEN momentum_score >= 65 AND momentum_score < 80 THEN 1 END) as medium_count,
                    COUNT(CASE WHEN momentum_score < 65 THEN 1 END) as low_count,
                    COUNT(DISTINCT token_id) as total_tokens
                FROM momentum_snapshots
                WHERE snapshot_at > $1 AND snapshot_at <= $2
                """,
                window_start,
                time_bucket,
            )

            liquidity_row = await conn.fetchrow(
                """
                SELECT AVG((features->>'liquidity_usd')::numeric) as avg_liquidity
                FROM momentum_snapshots
                WHERE snapshot_at > $1 AND snapshot_at <= $2
                AND features->>'liquidity_usd' IS NOT NULL
                """,
                window_start,
                time_bucket,
            )

        return {
            'time_bucket': time_bucket,
            'timeframe': timeframe,
            'avg_momentum_score': float(row['avg_score']) if row['avg_score'] else 0.0,
            'median_momentum_score': float(row['median_score']) if row['median_score'] else 0.0,
            'high_momentum_count': row['high_count'] or 0,
            'medium_momentum_count': row['medium_count'] or 0,
            'low_momentum_count': row['low_count'] or 0,
            'avg_liquidity_usd': float(liquidity_row['avg_liquidity']) if liquidity_row and liquidity_row['avg_liquidity'] else 0.0,
            'total_tokens_scanned': row['total_tokens'] or 0,
        }

    async def _compute_risk_aggregate(self, time_bucket: datetime, timeframe: str) -> dict:
        """Compute risk aggregate dari risk_snapshots."""
        window_start = time_bucket - self._get_window_delta(timeframe)

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(CASE WHEN risk_level = 'low' THEN 1 END) as low_count,
                    COUNT(CASE WHEN risk_level = 'medium' THEN 1 END) as medium_count,
                    COUNT(CASE WHEN risk_level = 'high' OR risk_level = 'critical' THEN 1 END) as high_count,
                    COUNT(CASE WHEN hard_block = true THEN 1 END) as hard_blocked_count,
                    AVG(coverage) as avg_coverage
                FROM risk_snapshots
                WHERE snapshot_at > $1 AND snapshot_at <= $2
                """,
                window_start,
                time_bucket,
            )

        return {
            'time_bucket': time_bucket,
            'timeframe': timeframe,
            'low_risk_count': row['low_count'] or 0,
            'medium_risk_count': row['medium_count'] or 0,
            'high_risk_count': row['high_count'] or 0,
            'hard_blocked_count': row['hard_blocked_count'] or 0,
            'avg_risk_coverage': float(row['avg_coverage']) if row['avg_coverage'] else 0.0,
        }

    def _get_window_delta(self, timeframe: str) -> timedelta:
        """Get timedelta untuk window."""
        if timeframe == '1h':
            return timedelta(hours=1)
        elif timeframe == '4h':
            return timedelta(hours=4)
        elif timeframe == '24h':
            return timedelta(hours=24)
        return timedelta(hours=1)

    async def _insert_momentum_aggregate(self, agg: dict) -> None:
        """Insert atau update momentum aggregate."""
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO momentum_aggregates 
                (time_bucket, timeframe, avg_momentum_score, median_momentum_score, 
                 high_momentum_count, medium_momentum_count, low_momentum_count, 
                 avg_liquidity_usd, total_tokens_scanned)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (time_bucket, timeframe) 
                DO UPDATE SET
                    avg_momentum_score = EXCLUDED.avg_momentum_score,
                    median_momentum_score = EXCLUDED.median_momentum_score,
                    high_momentum_count = EXCLUDED.high_momentum_count,
                    medium_momentum_count = EXCLUDED.medium_momentum_count,
                    low_momentum_count = EXCLUDED.low_momentum_count,
                    avg_liquidity_usd = EXCLUDED.avg_liquidity_usd,
                    total_tokens_scanned = EXCLUDED.total_tokens_scanned
                """,
                agg['time_bucket'],
                agg['timeframe'],
                agg['avg_momentum_score'],
                agg['median_momentum_score'],
                agg['high_momentum_count'],
                agg['medium_momentum_count'],
                agg['low_momentum_count'],
                agg['avg_liquidity_usd'],
                agg['total_tokens_scanned'],
            )

    async def _insert_risk_aggregate(self, agg: dict) -> None:
        """Insert atau update risk aggregate."""
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO risk_aggregates 
                (time_bucket, timeframe, low_risk_count, medium_risk_count, 
                 high_risk_count, hard_blocked_count, avg_risk_coverage)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (time_bucket, timeframe) 
                DO UPDATE SET
                    low_risk_count = EXCLUDED.low_risk_count,
                    medium_risk_count = EXCLUDED.medium_risk_count,
                    high_risk_count = EXCLUDED.high_risk_count,
                    hard_blocked_count = EXCLUDED.hard_blocked_count,
                    avg_risk_coverage = EXCLUDED.avg_risk_coverage
                """,
                agg['time_bucket'],
                agg['timeframe'],
                agg['low_risk_count'],
                agg['medium_risk_count'],
                agg['high_risk_count'],
                agg['hard_blocked_count'],
                agg['avg_risk_coverage'],
            )

    async def get_momentum_trend(
        self, timeframe: str, hours: int = 24
    ) -> list[dict]:
        """Return time-series momentum aggregates."""
        if not self.db.pool:
            return []

        end = datetime.now(UTC)
        start = end - timedelta(hours=hours)

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM momentum_aggregates
                WHERE timeframe = $1 AND time_bucket >= $2 AND time_bucket <= $3
                ORDER BY time_bucket ASC
                """,
                timeframe,
                start,
                end,
            )

        return [
            {
                'time_bucket': row['time_bucket'].isoformat(),
                'avg_momentum_score': float(row['avg_momentum_score']) if row['avg_momentum_score'] else 0.0,
                'median_momentum_score': float(row['median_momentum_score']) if row['median_momentum_score'] else 0.0,
                'high_momentum_count': row['high_momentum_count'],
                'medium_momentum_count': row['medium_momentum_count'],
                'low_momentum_count': row['low_momentum_count'],
                'total_tokens_scanned': row['total_tokens_scanned'],
            }
            for row in rows
        ]

    async def get_risk_trend(self, timeframe: str, hours: int = 24) -> list[dict]:
        """Return time-series risk aggregates."""
        if not self.db.pool:
            return []

        end = datetime.now(UTC)
        start = end - timedelta(hours=hours)

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM risk_aggregates
                WHERE timeframe = $1 AND time_bucket >= $2 AND time_bucket <= $3
                ORDER BY time_bucket ASC
                """,
                timeframe,
                start,
                end,
            )

        return [
            {
                'time_bucket': row['time_bucket'].isoformat(),
                'low_risk_count': row['low_risk_count'],
                'medium_risk_count': row['medium_risk_count'],
                'high_risk_count': row['high_risk_count'],
                'hard_blocked_count': row['hard_blocked_count'],
            }
            for row in rows
        ]

    async def get_top_tokens(self, category: str, limit: int = 10) -> list[dict]:
        """
        Category: high_momentum, watchlist, high_liquidity, new_pools
        """
        if not self.db.pool:
            return []

        query_map = {
            'high_momentum': """
                SELECT DISTINCT ON (ms.token_id)
                    t.id, t.chain, t.address, t.symbol, t.name,
                    ms.momentum_score, rs.risk_level
                FROM momentum_snapshots ms
                JOIN tokens t ON t.id = ms.token_id
                LEFT JOIN risk_snapshots rs ON rs.token_id = ms.token_id 
                    AND rs.snapshot_at = ms.snapshot_at
                WHERE ms.snapshot_at > NOW() - INTERVAL '1 hour'
                AND ms.momentum_score >= 80
                ORDER BY ms.token_id, ms.momentum_score DESC
                LIMIT $1
            """,
            'watchlist': """
                SELECT DISTINCT ON (ms.token_id)
                    t.id, t.chain, t.address, t.symbol, t.name,
                    ms.momentum_score, rs.risk_level
                FROM momentum_snapshots ms
                JOIN tokens t ON t.id = ms.token_id
                LEFT JOIN risk_snapshots rs ON rs.token_id = ms.token_id 
                    AND rs.snapshot_at = ms.snapshot_at
                WHERE ms.snapshot_at > NOW() - INTERVAL '1 hour'
                AND ms.momentum_score >= 65 AND ms.momentum_score < 80
                ORDER BY ms.token_id, ms.momentum_score DESC
                LIMIT $1
            """,
            'high_liquidity': """
                SELECT DISTINCT ON (t.id)
                    t.id, t.chain, t.address, t.symbol, t.name,
                    (market_snapshots.raw_data_ref->>'liquidity_usd')::numeric as liquidity_usd
                FROM tokens t
                JOIN market_snapshots ON market_snapshots.token_id = t.id
                WHERE market_snapshots.observed_at > NOW() - INTERVAL '1 hour'
                AND market_snapshots.raw_data_ref->>'liquidity_usd' IS NOT NULL
                ORDER BY t.id, (market_snapshots.raw_data_ref->>'liquidity_usd')::numeric DESC
                LIMIT $1
            """,
            'new_pools': """
                SELECT t.id, t.chain, t.address, t.symbol, t.name, t.first_seen_at
                FROM tokens t
                WHERE t.first_seen_at > NOW() - INTERVAL '24 hours'
                ORDER BY t.first_seen_at DESC
                LIMIT $1
            """,
        }

        query = query_map.get(category)
        if not query:
            return []

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [dict(row) for row in rows]

    async def get_overview(self) -> dict:
        """Dashboard overview stats."""
        if not self.db.pool:
            return {}

        async with self.db.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM tokens")
            scanned_24h = await conn.fetchval(
                "SELECT COUNT(DISTINCT token_id) FROM market_snapshots WHERE observed_at > NOW() - INTERVAL '24 hours'"
            )
            
            momentum_row = await conn.fetchrow(
                """
                SELECT AVG(momentum_score) as avg_score
                FROM momentum_snapshots
                WHERE snapshot_at > NOW() - INTERVAL '1 hour'
                """
            )
            
            risk_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(CASE WHEN risk_level = 'low' THEN 1 END) as low,
                    COUNT(CASE WHEN risk_level = 'medium' THEN 1 END) as medium,
                    COUNT(CASE WHEN risk_level = 'high' OR risk_level = 'critical' THEN 1 END) as high
                FROM risk_snapshots
                WHERE snapshot_at > NOW() - INTERVAL '1 hour'
                """
            )

        return {
            'total_tokens': total,
            'scanned_24h': scanned_24h,
            'avg_momentum_score': float(momentum_row['avg_score']) if momentum_row and momentum_row['avg_score'] else 0.0,
            'risk_distribution': {
                'low': risk_row['low'] if risk_row else 0,
                'medium': risk_row['medium'] if risk_row else 0,
                'high': risk_row['high'] if risk_row else 0,
            },
        }
