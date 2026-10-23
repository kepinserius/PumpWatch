from typing import Protocol

from pumpwatch.domain.models import MarketData, TokenInfo


class ProviderAdapter(Protocol):
    async def fetch_new_pairs(self, chain: str, limit: int = 50) -> list[TokenInfo]: ...

    async def fetch_market_data(self, chain: str, address: str) -> MarketData | None: ...

    async def health_check(self) -> tuple[bool, str]: ...
