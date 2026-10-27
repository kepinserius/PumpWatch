import logging
from datetime import UTC, datetime

from pumpwatch.config import settings
from pumpwatch.database import Database
from pumpwatch.domain.models import MarketData, TokenInfo
from pumpwatch.providers.dexscreener import DexScreenerAdapter
from pumpwatch.services.risk import RiskEngine
from pumpwatch.services.scoring import MomentumEngine

logger = logging.getLogger(__name__)

_momentum_engine = MomentumEngine()
_risk_engine = RiskEngine()


class IngestionService:
    def __init__(self, db: Database, provider: DexScreenerAdapter) -> None:
        self.db = db
        self.provider = provider

    async def scan_new_pairs(self, chain: str = "solana", limit: int = 50) -> list[TokenInfo]:
        logger.info(f"Scanning new pairs for chain: {chain}")
        pairs = await self.provider.fetch_new_pairs(chain, limit)
        logger.info(f"Found {len(pairs)} pairs")

        new_pairs: list[TokenInfo] = []
        for pair in pairs:
            if await self.db.is_token_seen(pair.chain, pair.address):
                continue
            new_pairs.append(pair)

        logger.info(f"{len(new_pairs)} new pairs to ingest")
        return new_pairs

    async def ingest_token(self, info: TokenInfo) -> tuple[int | None, int | None]:
        token_id = await self.db.upsert_token(info)
        pool_id = None
        if info.pool_address:
            pool_id = await self.db.upsert_pool(info)
        return token_id, pool_id

    async def ingest_market_data(self, data: MarketData) -> int | None:
        token_id = await self.db.get_token_id(data.chain, data.token_address)
        pool_id = None
        if data.pool_address:
            pool_id = await self.db.get_pool_id(data.chain, data.pool_address)

        if not token_id:
            logger.warning(f"Token not found: {data.token_address}")
            return None

        return await self.db.insert_snapshot(data, token_id, pool_id)

    async def scan_and_ingest(self, chain: str = "solana") -> int:
        import asyncio
        from dataclasses import replace as dc_replace
        pairs = await self.scan_new_pairs(chain)
        ingested = 0

        for pair in pairs:
            try:
                await asyncio.sleep(self.provider.rate_limit_delay)

                market_data = await self.provider.fetch_market_data(chain, pair.address)
                if not market_data:
                    logger.debug(f"No market data for {pair.address}, skipping")
                    continue

                raw_pair = market_data.raw_data if isinstance(market_data.raw_data, dict) else {}
                base = raw_pair.get("baseToken", {})
                enriched = dc_replace(
                    pair,
                    symbol=base.get("symbol") or pair.symbol,
                    name=base.get("name") or pair.name,
                    pool_address=market_data.pool_address or pair.pool_address,
                    dex_id=raw_pair.get("dexId") or pair.dex_id,
                    pool_created_at=(
                        self.provider._parse_timestamp(raw_pair.get("pairCreatedAt"))
                        or pair.pool_created_at
                    ),
                )

                token_id, pool_id = await self.ingest_token(enriched)
                if not token_id:
                    continue

                await self.ingest_market_data(market_data)
                ingested += 1
                logger.info(f"Ingested {enriched.symbol or pair.address[:8]} ({ingested} total)")

                # Scoring + signal generation
                await self._maybe_create_signal(market_data, token_id, pool_id)

            except Exception as e:
                logger.error(f"Error ingesting {pair.address}: {e}")
                continue

        logger.info(f"Scan selesai: {ingested} token diingested dari {len(pairs)} kandidat")
        return ingested

    async def _maybe_create_signal(
        self,
        market_data: MarketData,
        token_id: int,
        pool_id: int | None,
    ) -> None:
        """
        Hitung momentum score + risk. Jika score >= threshold dan tidak hard-block,
        insert signal ke DB (deduplicate: skip jika sudah ada signal aktif untuk token ini).
        """
        try:
            risk = _risk_engine.assess(market_data)
            score = _momentum_engine.calculate(market_data)

            sym = market_data.token_address[:8]
            logger.debug(
                f"Score {sym}: {score.total_score} | risk: {risk.risk_level} "
                f"(hard_block={risk.hard_block})"
            )

            # Hard-block mengalahkan momentum score
            if risk.hard_block:
                logger.info(f"Signal skipped ({sym}): hard-blocked, risk={risk.risk_level}")
                return

            if score.total_score < settings.momentum_threshold:
                logger.debug(
                    f"Signal skipped ({sym}): score {score.total_score} < threshold {settings.momentum_threshold}"
                )
                return

            # Cek apakah sudah ada signal aktif untuk token ini (deduplicate)
            already_active = await self._has_active_signal(token_id)
            if already_active:
                logger.debug(f"Signal skipped ({sym}): sudah ada signal aktif")
                return

            entry_price = float(market_data.price_usd) if market_data.price_usd else None
            signal_id = await self.db.insert_signal(token_id, pool_id, score, risk, entry_price)
            if signal_id:
                logger.info(
                    f"Signal created #{signal_id} untuk {sym}: "
                    f"score={score.total_score}, risk={risk.risk_level}"
                )
        except Exception as e:
            logger.error(f"Signal generation error untuk {market_data.token_address}: {e}")

    async def _has_active_signal(self, token_id: int) -> bool:
        """Cek apakah token sudah punya signal dengan status 'active'."""
        if not self.db.pool:
            return False
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM signals WHERE token_id = $1 AND status = 'active' LIMIT 1",
                token_id,
            )
            return row is not None

    async def rescore_existing_tokens(self, chain: str = "solana") -> int:
        """
        Re-fetch market data dan re-score semua token yang sudah ada di DB.
        Generate signal untuk token yang lolos threshold.
        Berguna untuk: populate signal pertama kali, atau re-evaluate setelah rule change.
        """
        import asyncio

        if not self.db.pool:
            return 0

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, address, symbol FROM tokens WHERE chain = $1 ORDER BY first_seen_at DESC",
                chain,
            )

        logger.info(f"Rescore: {len(rows)} token akan di-rescore untuk chain {chain}")
        signals_created = 0

        for row in rows:
            token_id = row["id"]
            address = row["address"]
            symbol = row["symbol"] or address[:8]
            try:
                await asyncio.sleep(self.provider.rate_limit_delay)
                market_data = await self.provider.fetch_market_data(chain, address)
                if not market_data:
                    logger.debug(f"Rescore: no market data for {symbol}, skipping")
                    continue

                pool_id = None
                if market_data.pool_address:
                    pool_id = await self.db.get_pool_id(chain, market_data.pool_address)

                before = signals_created
                await self._maybe_create_signal(market_data, token_id, pool_id)
                # Cek apakah signal baru dibuat dengan query count
                async with self.db.pool.acquire() as conn:
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM signals WHERE token_id = $1", token_id
                    )
                # Hitung dari perbedaan (approximasi, karena _maybe_create_signal tidak return count)
                _ = count  # digunakan untuk logging nanti

            except Exception as e:
                logger.error(f"Rescore error untuk {symbol}: {e}")
                continue

        # Hitung total signal yang berhasil dibuat dalam sesi ini
        async with self.db.pool.acquire() as conn:
            signals_created = await conn.fetchval(
                "SELECT COUNT(*) FROM signals WHERE created_at > NOW() - INTERVAL '5 minutes'"
            )

        logger.info(f"Rescore selesai: {signals_created} signal baru dibuat")
        return signals_created or 0

    def validate_market_data(self, data: MarketData) -> bool:
        if data.price_usd is not None and data.price_usd < 0:
            data.data_quality_status = "invalid_negative_price"
            return False

        if data.liquidity_usd is not None and data.liquidity_usd < settings.min_liquidity_usd:
            data.data_quality_status = "low_liquidity"
            return False

        now = datetime.now(UTC)
        age = (now - data.observed_at).total_seconds()
        if age > 300:
            data.data_quality_status = "stale"
            return False

        data.data_quality_status = "valid"
        return True
