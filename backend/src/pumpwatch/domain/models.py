from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class TokenInfo:
    chain: str
    address: str
    symbol: str | None = None
    name: str | None = None
    pool_address: str | None = None
    dex_id: str | None = None
    pool_created_at: datetime | None = None


@dataclass
class MarketData:
    chain: str
    token_address: str
    pool_address: str | None
    observed_at: datetime
    source: str
    price_usd: Decimal | None = None
    liquidity_usd: Decimal | None = None
    volume_5m: Decimal | None = None
    volume_1h: Decimal | None = None
    volume_6h: Decimal | None = None
    volume_24h: Decimal | None = None
    price_change_5m: Decimal | None = None
    price_change_1h: Decimal | None = None
    price_change_6h: Decimal | None = None
    price_change_24h: Decimal | None = None
    buys_5m: int | None = None
    buys_1h: int | None = None
    buys_6h: int | None = None
    buys_24h: int | None = None
    sells_5m: int | None = None
    sells_1h: int | None = None
    sells_6h: int | None = None
    sells_24h: int | None = None
    raw_data: dict[str, Any] | None = None
    data_quality_status: str = "valid"
