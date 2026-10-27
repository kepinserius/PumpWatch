import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from pumpwatch.config import settings
from pumpwatch.domain.models import MarketData, TokenInfo

logger = logging.getLogger(__name__)


class DexScreenerAdapter:
    # DexScreener punya dua basis URL:
    # - /latest/dex/* → untuk data pair & token
    # - /* (root) → untuk token-profiles, token-boosts, dsb
    DEXSCREENER_ROOT = "https://api.dexscreener.com"

    def __init__(self) -> None:
        self.base_url = settings.dex_screener_api_url  # e.g. https://api.dexscreener.com/latest
        self.timeout = settings.request_timeout
        self.rate_limit_delay = settings.rate_limit_delay

    async def _fetch(self, client: httpx.AsyncClient, path: str) -> dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        try:
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()
            raw = response.json()
            return raw if isinstance(raw, dict) else None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {e}")
            return None

    async def _fetch_list(self, client: httpx.AsyncClient, path: str) -> list[Any] | None:
        """Fetch endpoint yang mengembalikan JSON array."""
        url = f"{self.base_url}{path}"
        try:
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()
            raw = response.json()
            return raw if isinstance(raw, list) else None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {e}")
            return None

    async def fetch_new_pairs(self, chain: str, limit: int = 50) -> list[TokenInfo]:
        """
        Fetch recently active tokens dari DexScreener token-profiles endpoint.
        Endpoint: GET https://api.dexscreener.com/token-profiles/latest/v1
        (Beda basis dari /latest/dex/* — tidak pakai self.base_url)
        """
        url = f"{self.DEXSCREENER_ROOT}/token-profiles/latest/v1"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.warning(f"fetch_new_pairs error: {e}")
                return []

            if not isinstance(data, list):
                logger.warning(f"fetch_new_pairs: unexpected response type {type(data)}")
                return []

            chain_lower = chain.lower()
            filtered = [
                item for item in data
                if item.get("chainId", "").lower() == chain_lower
                and item.get("tokenAddress")
            ][:limit]

            logger.info(f"fetch_new_pairs: {len(filtered)} {chain} tokens dari token-profiles")

            return [
                TokenInfo(
                    chain=chain_lower,
                    address=item["tokenAddress"],
                    symbol=None,
                    name=None,
                    pool_address=None,
                    dex_id=None,
                    pool_created_at=None,
                )
                for item in filtered
            ]


    async def fetch_market_data(self, chain: str, address: str) -> MarketData | None:
        async with httpx.AsyncClient() as client:
            data = await self._fetch(client, f"/dex/tokens/{address}")
            if not data:
                return None
            pairs = data.get("pairs") or []
            if not pairs:
                return None
            pair = pairs[0]
            return self._parse_pair_to_market_data(pair, chain, address)

    async def health_check(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}", timeout=5.0)
                return response.status_code < 500, "ok" if response.status_code < 500 else "error"
        except Exception as e:
            return False, str(e)

    def _parse_timestamp(self, ts: int | None) -> datetime | None:
        if ts is None:
            return None
        return datetime.fromtimestamp(ts / 1000, tz=UTC)

    def _parse_pair_to_market_data(
        self, pair: dict[str, Any], chain: str, address: str
    ) -> MarketData:
        volume = pair.get("volume", {}) or {}
        tx = pair.get("txns", {}) or {}
        price_change = pair.get("priceChange", {}) or {}

        def safe_decimal(val: Any) -> Decimal | None:
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except Exception:
                return None

        def safe_int(val: dict[str, Any] | None, key: str) -> int | None:
            if val is None or key not in val:
                return None
            try:
                return int(val[key])
            except Exception:
                return None

        return MarketData(
            chain=chain.lower(),
            token_address=address,
            pool_address=pair.get("pairAddress"),
            observed_at=datetime.now(UTC),
            source="dexscreener",
            price_usd=safe_decimal(pair.get("priceUsd")),
            liquidity_usd=safe_decimal(pair.get("liquidity", {}).get("usd")) if pair.get("liquidity") else None,
            volume_5m=safe_decimal(volume.get("m5")),
            volume_1h=safe_decimal(volume.get("h1")),
            volume_6h=safe_decimal(volume.get("h6")),
            volume_24h=safe_decimal(volume.get("h24")),
            price_change_5m=safe_decimal(price_change.get("m5")),
            price_change_1h=safe_decimal(price_change.get("h1")),
            price_change_6h=safe_decimal(price_change.get("h6")),
            price_change_24h=safe_decimal(price_change.get("h24")),
            buys_5m=safe_int(tx.get("m5"), "buys"),
            buys_1h=safe_int(tx.get("h1"), "buys"),
            buys_6h=safe_int(tx.get("h6"), "buys"),
            buys_24h=safe_int(tx.get("h24"), "buys"),
            sells_5m=safe_int(tx.get("m5"), "sells"),
            sells_1h=safe_int(tx.get("h1"), "sells"),
            sells_6h=safe_int(tx.get("h6"), "sells"),
            sells_24h=safe_int(tx.get("h24"), "sells"),
            raw_data=pair,
        )
