from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pumpwatch.database import Database
from pumpwatch.domain.scoring import MomentumScore
from pumpwatch.services.archiver import DataArchiver

router = APIRouter()


class HistoricalMomentumResponse(BaseModel):
    snapshot_at: str
    momentum_score: float
    score_components: list[dict]
    data_coverage: float | None
    rules_version: str


class HistoricalRiskResponse(BaseModel):
    snapshot_at: str
    risk_level: str
    hard_block: bool
    flags: list[dict]
    coverage: float | None
    rules_version: str


@router.get("/tokens/{chain}/{address}/momentum-history", response_model=list[HistoricalMomentumResponse])
async def get_momentum_history(
    chain: str,
    address: str,
    hours: int = 24,
) -> list[dict]:
    """
    Return momentum score time-series untuk token.
    Default 24 jam terakhir.
    """
    if hours <= 0:
        raise HTTPException(status_code=400, detail="hours must be positive")
    if hours > 720:
        raise HTTPException(status_code=400, detail="hours must be <= 720 (30 days)")

    end = datetime.now()
    start = end - timedelta(hours=hours)

    from pumpwatch.main import db, archiver

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    token_id = await db.get_token_id(chain, address)
    if not token_id:
        raise HTTPException(status_code=404, detail=f"Token {chain}/{address} not found")

    snapshots = await archiver.get_historical_momentum(token_id, start, end)
    return snapshots


@router.get("/tokens/{chain}/{address}/risk-history", response_model=list[HistoricalRiskResponse])
async def get_risk_history(
    chain: str,
    address: str,
    hours: int = 24,
) -> list[dict]:
    """
    Return risk level time-series untuk token.
    Default 24 jam terakhir.
    """
    if hours <= 0:
        raise HTTPException(status_code=400, detail="hours must be positive")
    if hours > 720:
        raise HTTPException(status_code=400, detail="hours must be <= 720 (30 days)")

    end = datetime.now()
    start = end - timedelta(hours=hours)

    from pumpwatch.main import db, archiver

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    token_id = await db.get_token_id(chain, address)
    if not token_id:
        raise HTTPException(status_code=404, detail=f"Token {chain}/{address} not found")

    snapshots = await archiver.get_historical_risk(token_id, start, end)
    return snapshots


@router.post("/admin/cleanup-snapshots")
async def cleanup_snapshots(retention_days: int = 90) -> dict:
    """
    Clean up old snapshots. Admin endpoint.
    """
    if retention_days <= 0:
        raise HTTPException(status_code=400, detail="retention_days must be positive")
    if retention_days > 365:
        raise HTTPException(status_code=400, detail="retention_days must be <= 365")

    from pumpwatch.main import archiver

    if not archiver:
        raise HTTPException(status_code=503, detail="Archiver not initialized")

    deleted = await archiver.cleanup_old_snapshots(retention_days)
    return {
        "status": "success",
        "retention_days": retention_days,
        "total_deleted": deleted,
    }
