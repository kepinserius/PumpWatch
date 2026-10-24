import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from pumpwatch.api.router import init_router, router
from pumpwatch.config import settings
from pumpwatch.database import Database
from pumpwatch.logging_config import setup_logging
from pumpwatch.providers.dexscreener import DexScreenerAdapter
from pumpwatch.services.ingestion import IngestionService

setup_logging()

logger = logging.getLogger(__name__)

db = Database(settings.database_url)
provider = DexScreenerAdapter()
ingestion = IngestionService(db, provider)

app = FastAPI(title="PumpWatch API", version="0.1.0")

init_router(db, provider, ingestion)
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup() -> None:
    await db.connect()
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown() -> None:
    await db.disconnect()
    logger.info("Application stopped")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, Any]:
    try:
        if db.pool:
            async with db.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        db_status = "disconnected"

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/providers/health")
async def providers_health() -> dict[str, Any]:
    is_healthy, message = await provider.health_check()
    return {
        "provider": "dexscreener",
        "status": "healthy" if is_healthy else "unhealthy",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/admin/scan")
async def trigger_scan(chain: str = "solana", api_key: str = "") -> dict[str, Any]:
    if settings.admin_api_key and api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    logger.info(f"Manual scan triggered for chain: {chain}")
    count = await ingestion.scan_and_ingest(chain)
    return {
        "chain": chain,
        "tokens_ingested": count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
