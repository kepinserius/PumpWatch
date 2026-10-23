import logging
from datetime import UTC, datetime

from pumpwatch.config import settings
from pumpwatch.database import Database
from pumpwatch.domain.models import MarketData, TokenInfo
from pumpwatch.providers.dexscreener import DexScreenerAdapter

logger = logging.getLogger(__name__)


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
        pairs = await self.scan_new_pairs(chain)
        ingested = 0

        for pair in pairs:
            token_id, pool_id = await self.ingest_token(pair)
            if not token_id:
                continue

            market_data = await self.provider.fetch_market_data(chain, pair.address)
            if market_data:
                await self.ingest_market_data(market_data)
                ingested += 1

        logger.info(f"Ingested {ingested} tokens")
        return ingested

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
