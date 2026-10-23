from fastapi import APIRouter, HTTPException

from pumpwatch.database import Database
from pumpwatch.providers.dexscreener import DexScreenerAdapter
from pumpwatch.services.ingestion import IngestionService
from pumpwatch.services.risk import RiskEngine
from pumpwatch.services.scoring import MomentumEngine

router = APIRouter()

db: Database | None = None
provider: DexScreenerAdapter | None = None
ingestion: IngestionService | None = None


def init_router(database: Database, prov: DexScreenerAdapter, ing: IngestionService) -> None:
    global db, provider, ingestion
    db = database
    provider = prov
    ingestion = ing


@router.get("/tokens")
async def list_tokens(chain: str | None = None, limit: int = 50, offset: int = 0):
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT t.chain, t.address, t.symbol, t.name,
                   MAX(ms.observed_at) as last_seen,
                   COUNT(ms.id) as snapshot_count
            FROM tokens t
            LEFT JOIN market_snapshots ms ON t.id = ms.token_id
            WHERE ($1 IS NULL OR t.chain = $1)
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
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    async with db.pool.acquire() as conn:
        token = await conn.fetchrow(
            "SELECT * FROM tokens WHERE chain = $1 AND address = $2",
            chain,
            address,
        )
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        return dict(token)


@router.get("/tokens/{chain}/{address}/score")
async def get_token_score(chain: str, address: str):
    if not provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    data = await provider.fetch_market_data(chain, address)
    if not data:
        raise HTTPException(status_code=404, detail="Market data not found")

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
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT ms.*, t.address as token_address
            FROM market_snapshots ms
            JOIN tokens t ON ms.token_id = t.id
            WHERE t.chain = $1 AND t.address = $2
            ORDER BY ms.observed_at DESC
            LIMIT $3
            """,
            chain,
            address,
            limit,
        )
        return [dict(row) for row in rows]
