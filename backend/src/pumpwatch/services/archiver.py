import logging
from datetime import UTC, datetime, timedelta

from pumpwatch.config import settings
from pumpwatch.database import Database
from pumpwatch.domain.models import MarketData
from pumpwatch.domain.risk import RiskAssessment
from pumpwatch.domain.scoring import MomentumScore
from pumpwatch.services.risk import RiskEngine
from pumpwatch.services.scoring import MomentumEngine

logger = logging.getLogger(__name__)


class DataArchiver:
    def __init__(self, db: Database):
        self.db = db
        self.momentum_engine = MomentumEngine()
        self.risk_engine = RiskEngine()
        self.snapshot_interval_minutes = settings.archive_interval_minutes
        self.retention_days = settings.archive_retention_days

    async def archive_current_scores(self) -> int:
        """
        Archive momentum + risk scores untuk semua active tokens.
        Return: jumlah tokens yang di-archive.
        """
        if not self.db.pool:
            logger.warning("Database pool not available, skipping archive")
            return 0

        active_tokens = await self._get_active_tokens()
        archived_count = 0

        for token in active_tokens:
            try:
                market_data = await self._get_latest_market_data(token["id"])
                if not market_data:
                    logger.debug(f"No market data for token_id={token['id']}, skipping")
                    continue

                score = self.momentum_engine.calculate(market_data)
                risk = self.risk_engine.assess(market_data)

                should_archive = await self._should_archive(token["id"], score, risk)
                if not should_archive:
                    logger.debug(f"Skipping duplicate snapshot for token_id={token['id']}")
                    continue

                await self._insert_momentum_snapshot(token["id"], token.get("pool_id"), score)
                await self._insert_risk_snapshot(token["id"], token.get("pool_id"), risk)

                archived_count += 1
                logger.debug(f"Archived token_id={token['id']} (score={score.total_score})")

            except Exception as e:
                logger.error(f"Error archiving token_id={token['id']}: {e}")
                continue

        logger.info(f"Archive completed: {archived_count} tokens archived")
        return archived_count

    async def _get_active_tokens(self) -> list[dict]:
        """Get tokens yang terlihat dalam 2 jam terakhir."""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT t.id, t.chain, t.address, p.id as pool_id
                FROM tokens t
                LEFT JOIN pools p ON p.base_token_address = t.address AND p.chain = t.chain
                LEFT JOIN market_snapshots ms ON ms.token_id = t.id
                WHERE ms.observed_at > NOW() - INTERVAL '2 hours'
                ORDER BY t.id
                """
            )
            return [dict(row) for row in rows]

    async def _get_latest_market_data(self, token_id: int) -> MarketData | None:
        """Get latest market snapshot untuk token."""
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    t.chain, t.address, ms.*
                FROM market_snapshots ms
                JOIN tokens t ON t.id = ms.token_id
                WHERE ms.token_id = $1
                ORDER BY ms.observed_at DESC
                LIMIT 1
                """,
                token_id,
            )
            if not row:
                return None

            return MarketData(
                chain=row["chain"],
                token_address=row["address"],
                pool_address=None,
                dex_id=row["source"],
                price_usd=float(row["price_usd"]) if row["price_usd"] else None,
                liquidity_usd=float(row["liquidity_usd"]) if row["liquidity_usd"] else None,
                volume_5m=float(row["volume_5m"]) if row["volume_5m"] else None,
                volume_1h=float(row["volume_1h"]) if row["volume_1h"] else None,
                volume_6h=float(row["volume_6h"]) if row["volume_6h"] else None,
                volume_24h=float(row["volume_24h"]) if row["volume_24h"] else None,
                price_change_5m=float(row["price_change_5m"]) if row["price_change_5m"] else None,
                price_change_1h=float(row["price_change_1h"]) if row["price_change_1h"] else None,
                price_change_6h=float(row["price_change_6h"]) if row["price_change_6h"] else None,
                price_change_24h=float(row["price_change_24h"]) if row["price_change_24h"] else None,
                buys_5m=row["buys_5m"],
                buys_1h=row["buys_1h"],
                buys_6h=row["buys_6h"],
                buys_24h=row["buys_24h"],
                sells_5m=row["sells_5m"],
                sells_1h=row["sells_1h"],
                sells_6h=row["sells_6h"],
                sells_24h=row["sells_24h"],
                pool_created_at=row["observed_at"],
                raw_data={},
            )

    async def _should_archive(
        self, token_id: int, score: MomentumScore, risk: RiskAssessment
    ) -> bool:
        """
        Check apakah snapshot berbeda dari yang terakhir (deduplication).
        Return True jika perlu di-archive.
        """
        async with self.db.pool.acquire() as conn:
            last_momentum = await conn.fetchrow(
                """
                SELECT momentum_score, risk_level
                FROM momentum_snapshots ms
                LEFT JOIN risk_snapshots rs ON rs.token_id = ms.token_id 
                    AND rs.snapshot_at = ms.snapshot_at
                WHERE ms.token_id = $1
                ORDER BY ms.snapshot_at DESC
                LIMIT 1
                """,
                token_id,
            )

            if not last_momentum:
                return True

            score_changed = abs(float(last_momentum["momentum_score"]) - score.total_score) >= 1.0
            risk_changed = last_momentum.get("risk_level") != risk.risk_level

            return score_changed or risk_changed

    async def _insert_momentum_snapshot(
        self, token_id: int, pool_id: int | None, score: MomentumScore
    ):
        """Insert momentum snapshot."""
        import json

        components_json = json.dumps(
            [
                {
                    "name": c.name,
                    "score": c.score,
                    "weight": c.weight,
                    "details": c.details,
                }
                for c in score.components
            ]
        )
        features_json = json.dumps(score.features) if isinstance(score.features, dict) else score.features

        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO momentum_snapshots 
                (token_id, pool_id, snapshot_at, momentum_score, score_components, 
                 features, data_coverage, rules_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                token_id,
                pool_id,
                datetime.now(UTC),
                score.total_score,
                components_json,
                features_json,
                score.data_coverage,
                score.rules_version,
            )

    async def _insert_risk_snapshot(
        self, token_id: int, pool_id: int | None, risk: RiskAssessment
    ):
        """Insert risk snapshot."""
        import json

        flags_json = json.dumps(
            [
                {
                    "name": f.name,
                    "status": f.status,
                    "severity": f.severity,
                    "reason": f.reason,
                }
                for f in risk.flags
            ]
        )

        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO risk_snapshots 
                (token_id, pool_id, snapshot_at, risk_level, hard_block, 
                 flags, coverage, rules_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                token_id,
                pool_id,
                datetime.now(UTC),
                risk.risk_level,
                risk.hard_block,
                flags_json,
                risk.coverage,
                risk.rules_version,
            )

    async def get_historical_momentum(
        self, token_id: int, start: datetime, end: datetime
    ) -> list[dict]:
        """Query momentum snapshots untuk chart historis."""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    snapshot_at, momentum_score, score_components, 
                    data_coverage, rules_version
                FROM momentum_snapshots
                WHERE token_id = $1 
                AND snapshot_at >= $2 
                AND snapshot_at <= $3
                ORDER BY snapshot_at ASC
                """,
                token_id,
                start,
                end,
            )
            return [
                {
                    "snapshot_at": row["snapshot_at"].isoformat(),
                    "momentum_score": float(row["momentum_score"]),
                    "score_components": row["score_components"],
                    "data_coverage": float(row["data_coverage"]) if row["data_coverage"] else None,
                    "rules_version": row["rules_version"],
                }
                for row in rows
            ]

    async def get_historical_risk(
        self, token_id: int, start: datetime, end: datetime
    ) -> list[dict]:
        """Query risk snapshots untuk chart historis."""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    snapshot_at, risk_level, hard_block, flags, 
                    coverage, rules_version
                FROM risk_snapshots
                WHERE token_id = $1 
                AND snapshot_at >= $2 
                AND snapshot_at <= $3
                ORDER BY snapshot_at ASC
                """,
                token_id,
                start,
                end,
            )
            return [
                {
                    "snapshot_at": row["snapshot_at"].isoformat(),
                    "risk_level": row["risk_level"],
                    "hard_block": row["hard_block"],
                    "flags": row["flags"],
                    "coverage": float(row["coverage"]) if row["coverage"] else None,
                    "rules_version": row["rules_version"],
                }
                for row in rows
            ]

    async def cleanup_old_snapshots(self, retention_days: int | None = None) -> int:
        """
        Hapus snapshots lama sesuai retention policy.
        Return: jumlah records yang dihapus.
        """
        days = retention_days or self.retention_days
        cutoff = datetime.now(UTC) - timedelta(days=days)

        async with self.db.pool.acquire() as conn:
            momentum_deleted = await conn.execute(
                "DELETE FROM momentum_snapshots WHERE snapshot_at < $1",
                cutoff,
            )
            risk_deleted = await conn.execute(
                "DELETE FROM risk_snapshots WHERE snapshot_at < $1",
                cutoff,
            )

        momentum_count = int(momentum_deleted.split()[-1])
        risk_count = int(risk_deleted.split()[-1])
        total = momentum_count + risk_count

        logger.info(f"Cleanup completed: {total} old snapshots deleted (retention={days}d)")
        return total
