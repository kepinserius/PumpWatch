import logging
from datetime import UTC, datetime

import asyncpg

from pumpwatch.domain.models import MarketData, TokenInfo
from pumpwatch.domain.risk import RiskAssessment
from pumpwatch.domain.scoring import MomentumScore

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        logger.info("Database connected")

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            logger.info("Database disconnected")

    async def upsert_token(self, info: TokenInfo) -> int | None:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO tokens (chain, address, symbol, name, first_seen_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (chain, address) DO UPDATE SET
                    symbol = COALESCE(EXCLUDED.symbol, tokens.symbol),
                    name = COALESCE(EXCLUDED.name, tokens.name)
                RETURNING id
                """,
                info.chain,
                info.address,
                info.symbol,
                info.name,
            )
            return row["id"] if row else None

    async def upsert_pool(self, info: TokenInfo) -> int | None:
        if not self.pool or not info.pool_address:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO pools (chain, pool_address, base_token_address, quote_token_address, dex_id, created_at, first_seen_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (chain, pool_address) DO UPDATE SET
                    dex_id = COALESCE(EXCLUDED.dex_id, pools.dex_id),
                    created_at = COALESCE(EXCLUDED.created_at, pools.created_at)
                RETURNING id
                """,
                info.chain,
                info.pool_address,
                info.address,
                "So11111111111111111111111111111111111111112",
                info.dex_id,
                info.pool_created_at,
            )
            return row["id"] if row else None

    async def insert_snapshot(
        self, data: MarketData, token_id: int | None, pool_id: int | None
    ) -> int | None:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO market_snapshots (
                    token_id, pool_id, observed_at, source,
                    price_usd, liquidity_usd,
                    volume_5m, volume_1h, volume_6h, volume_24h,
                    price_change_5m, price_change_1h, price_change_6h, price_change_24h,
                    buys_5m, buys_1h, buys_6h, buys_24h,
                    sells_5m, sells_1h, sells_6h, sells_24h,
                    raw_data_ref, data_quality_status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
                ) RETURNING id
                """,
                token_id,
                pool_id,
                data.observed_at,
                data.source,
                data.price_usd,
                data.liquidity_usd,
                data.volume_5m,
                data.volume_1h,
                data.volume_6h,
                data.volume_24h,
                data.price_change_5m,
                data.price_change_1h,
                data.price_change_6h,
                data.price_change_24h,
                data.buys_5m,
                data.buys_1h,
                data.buys_6h,
                data.buys_24h,
                data.sells_5m,
                data.sells_1h,
                data.sells_6h,
                data.sells_24h,
                data.raw_data,
                data.data_quality_status,
            )
            return row["id"] if row else None

    async def insert_signal(
        self,
        token_id: int,
        pool_id: int | None,
        score: MomentumScore,
        risk: RiskAssessment,
        entry_price: float | None,
    ) -> int | None:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO signals (
                    token_id, pool_id, created_at, score,
                    score_components_json, feature_snapshot_json,
                    risk_assessment_json, rules_version, entry_price_usd
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                token_id,
                pool_id,
                datetime.now(UTC),
                score.total_score,
                {
                    "components": [
                        {"name": c.name, "score": c.score, "weight": c.weight, "details": c.details}
                        for c in score.components
                    ],
                    "data_coverage": score.data_coverage,
                },
                score.features,
                {
                    "risk_level": risk.risk_level,
                    "hard_block": risk.hard_block,
                    "flags": [
                        {
                            "name": f.name,
                            "status": f.status,
                            "severity": f.severity,
                            "reason": f.reason,
                        }
                        for f in risk.flags
                    ],
                    "coverage": risk.coverage,
                },
                score.rules_version,
                entry_price,
            )
            return row["id"] if row else None

    async def insert_alert(self, signal_id: int, channel: str, dedupe_key: str) -> int | None:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO alerts (signal_id, channel, dedupe_key, sent_at, status)
                VALUES ($1, $2, $3, NOW(), 'sent')
                ON CONFLICT (dedupe_key) DO NOTHING
                RETURNING id
                """,
                signal_id,
                channel,
                dedupe_key,
            )
            return row["id"] if row else None

    async def get_token_id(self, chain: str, address: str) -> int | None:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM tokens WHERE chain = $1 AND address = $2",
                chain,
                address,
            )
            return row["id"] if row else None

    async def get_pool_id(self, chain: str, pool_address: str) -> int | None:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM pools WHERE chain = $1 AND pool_address = $2",
                chain,
                pool_address,
            )
            return row["id"] if row else None

    async def is_token_seen(self, chain: str, address: str, since_hours: int = 24) -> bool:
        if not self.pool:
            return False
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 1 FROM tokens
                WHERE chain = $1 AND address = $2
                AND first_seen_at > NOW() - INTERVAL '%s hours'
                """,
                chain,
                address,
            )
            return row is not None
