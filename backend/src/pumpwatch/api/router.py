from fastapi import APIRouter, HTTPException

from pumpwatch.config import settings
from pumpwatch.database import Database
from pumpwatch.providers.dexscreener import DexScreenerAdapter
from pumpwatch.services.ingestion import IngestionService

router = APIRouter()

_db: Database | None = None
_provider: DexScreenerAdapter | None = None
_ingestion: IngestionService | None = None


async def _get_db() -> Database:
    global _db
    if not _db:
        _db = Database(settings.database_url)
        await _db.connect()
    return _db


async def _get_provider() -> DexScreenerAdapter:
    global _provider
    if not _provider:
        _provider = DexScreenerAdapter()
    return _provider


async def _get_ingestion() -> IngestionService:
    global _ingestion
    if not _ingestion:
        db = await _get_db()
        provider = await _get_provider()
        _ingestion = IngestionService(db, provider)
    return _ingestion


@router.get("/tokens")
async def list_tokens(chain: str | None = None, limit: int = 50, offset: int = 0):
    db = await _get_db()
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT t.chain, t.address, t.symbol, t.name,
                   MAX(ms.observed_at) as last_seen,
                   COUNT(ms.id) as snapshot_count
            FROM tokens t
            LEFT JOIN market_snapshots ms ON t.id = ms.token_id
            WHERE ($1::varchar IS NULL OR t.chain = $1)
            GROUP BY t.id
            ORDER BY last_seen DESC NULLS LAST
            LIMIT $2 OFFSET $3
            """,
            chain,
            limit,
            offset,
        )
        return [dict(row) for row in rows]


@router.get("/tokens/{chain}/{address}")
async def get_token(chain: str, address: str):
    db = await _get_db()
    async with db.pool.acquire() as conn:
        token = await conn.fetchrow(
            "SELECT * FROM tokens WHERE chain = $1::varchar AND address = $2::varchar",
            chain,
            address,
        )
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        return dict(token)


@router.get("/tokens/{chain}/{address}/score")
async def get_token_score(chain: str, address: str):
    provider = await _get_provider()
    data = await provider.fetch_market_data(chain, address)
    if not data:
        raise HTTPException(status_code=404, detail="Market data not found")

    from pumpwatch.services.risk import RiskEngine
    from pumpwatch.services.scoring import MomentumEngine

    risk_engine = RiskEngine()
    risk = risk_engine.assess(data)

    momentum_engine = MomentumEngine()
    score = momentum_engine.calculate(data)

    return {
        "token": {"chain": data.chain, "address": data.token_address},
        "risk": {
            "level": risk.risk_level,
            "hard_block": risk.hard_block,
            "flags": [{"name": f.name, "status": f.status, "severity": f.severity, "reason": f.reason} for f in risk.flags],
            "coverage": risk.coverage,
        },
        "momentum": {
            "score": score.total_score,
            "components": [{"name": c.name, "score": c.score, "weight": c.weight} for c in score.components],
            "data_coverage": score.data_coverage,
        },
    }


@router.get("/tokens/{chain}/{address}/snapshots")
async def get_snapshots(chain: str, address: str, limit: int = 20):
    db = await _get_db()
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT ms.*, t.address as token_address
            FROM market_snapshots ms
            JOIN tokens t ON ms.token_id = t.id
            WHERE t.chain = $1::varchar AND t.address = $2::varchar
            ORDER BY ms.observed_at DESC
            LIMIT $3
            """,
            chain,
            address,
            limit,
        )
        return [dict(row) for row in rows]


@router.get("/signals")
async def list_signals(
    chain: str | None = None, status: str | None = None, limit: int = 50, offset: int = 0
):
    db = await _get_db()
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT s.id, s.created_at, s.score, s.status, s.entry_price_usd,
                   t.chain, t.address, t.symbol, t.name
            FROM signals s
            JOIN tokens t ON s.token_id = t.id
            WHERE ($1::varchar IS NULL OR t.chain = $1)
            AND ($2::varchar IS NULL OR s.status = $2)
            ORDER BY s.created_at DESC
            LIMIT $3 OFFSET $4
            """,
            chain,
            status,
            limit,
            offset,
        )
        return [dict(row) for row in rows]


@router.get("/signals/{signal_id}")
async def get_signal(signal_id: int):
    db = await _get_db()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.*, t.chain, t.address, t.symbol, t.name
            FROM signals s
            JOIN tokens t ON s.token_id = t.id
            WHERE s.id = $1
            """,
            signal_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Signal not found")
        return dict(row)


@router.get("/signals/{signal_id}/outcome")
async def get_signal_outcome(signal_id: int):
    db = await _get_db()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM signal_outcomes WHERE signal_id = $1",
            signal_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Outcome not found")
        return dict(row)


@router.get("/paper-trades")
async def list_paper_trades(limit: int = 100):
    db = await _get_db()
    from pumpwatch.services.paper_trade import PaperTrader

    trader = PaperTrader(db)
    trades = await trader.get_trade_history(limit)
    return trades


@router.get("/paper-trades/open")
async def list_open_positions():
    db = await _get_db()
    from pumpwatch.services.paper_trade import PaperTrader

    trader = PaperTrader(db)
    positions = await trader.get_open_positions()
    return positions
