from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pumpwatch.services.backtest import BacktestEngine

router = APIRouter()


class BacktestRunRequest(BaseModel):
    name: str
    start_date: str
    end_date: str
    fee_percent: float = 0.01
    slippage_percent: float = 0.005
    strategy: str = "time_based"
    exit_hours: int = 4


@router.post("/backtest/run")
async def create_backtest_run(config: BacktestRunRequest) -> dict:
    """Buat dan jalankan backtest baru."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        start = datetime.fromisoformat(config.start_date)
        end = datetime.fromisoformat(config.end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")

    if start >= end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    engine = BacktestEngine(db)
    run_id = await engine.run_backtest(
        name=config.name,
        start_date=start,
        end_date=end,
        fee_percent=config.fee_percent,
        slippage_percent=config.slippage_percent,
        strategy=config.strategy,
        exit_hours=config.exit_hours,
    )

    return {"status": "completed", "run_id": run_id}


@router.get("/backtest/runs")
async def list_backtest_runs(limit: int = 20, offset: int = 0) -> list[dict]:
    """List semua backtest runs dengan pagination."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    engine = BacktestEngine(db)
    return await engine.list_backtest_runs(limit, offset)


@router.get("/backtest/runs/{run_id}")
async def get_backtest_result(run_id: int) -> dict:
    """Detail hasil backtest + metrics."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    engine = BacktestEngine(db)
    try:
        return await engine.get_backtest_results(run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/backtest/runs/{run_id}/trades")
async def get_backtest_trades(run_id: int, limit: int = 50) -> list[dict]:
    """List trades dari backtest tertentu."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    engine = BacktestEngine(db)
    return await engine.get_backtest_trades(run_id, limit)
