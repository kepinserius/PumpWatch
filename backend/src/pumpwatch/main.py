import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException

from pumpwatch.api.router import router
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

_scanner_task: asyncio.Task | None = None


async def _background_scanner() -> None:
    """
    Loop background yang scan token secara periodik.
    Jalan terus sampai server dimatikan.
    """
    interval = settings.scan_interval_minutes * 60  # detik

    if settings.scan_on_startup:
        logger.info("Background scanner: scan pertama saat startup...")
        try:
            count = await ingestion.scan_and_ingest("solana")
            logger.info(f"Startup scan selesai: {count} token diingested")
        except Exception as e:
            logger.error(f"Startup scan error: {e}")

    if interval <= 0:
        logger.info("Background scanner: SCAN_INTERVAL_MINUTES=0, periodic scan dinonaktifkan")
        return

    logger.info(f"Background scanner: akan scan ulang setiap {settings.scan_interval_minutes} menit")
    while True:
        await asyncio.sleep(interval)
        logger.info("Background scanner: memulai scan periodik...")
        try:
            count = await ingestion.scan_and_ingest("solana")
            logger.info(f"Scan periodik selesai: {count} token diingested, next in {settings.scan_interval_minutes}m")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Scan periodik error (akan retry di interval berikutnya): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scanner_task

    # ── Startup ──────────────────────────────────────────────────
    await db.connect()
    logger.info("Database connected")

    _scanner_task = asyncio.create_task(_background_scanner())
    logger.info("Background scanner task started")

    yield  # aplikasi berjalan

    # ── Shutdown ─────────────────────────────────────────────────
    if _scanner_task and not _scanner_task.done():
        _scanner_task.cancel()
        try:
            await _scanner_task
        except asyncio.CancelledError:
            pass
        logger.info("Background scanner task stopped")

    await db.disconnect()
    logger.info("Application stopped")


app = FastAPI(title="PumpWatch API", version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api/v1")


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

    scanner_status = "running"
    if _scanner_task is None:
        scanner_status = "not_started"
    elif _scanner_task.done():
        scanner_status = "stopped"

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "scanner": scanner_status,
        "scan_interval_minutes": settings.scan_interval_minutes,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/v1/providers/health")
async def providers_health() -> dict[str, Any]:
    is_healthy, message = await provider.health_check()
    return {
        "provider": "dexscreener",
        "status": "healthy" if is_healthy else "unhealthy",
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
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
        "timestamp": datetime.now(UTC).isoformat(),
    }




@app.post("/api/v1/admin/rescore")
async def trigger_rescore(chain: str = "solana", api_key: str = "") -> dict[str, Any]:
    """Re-score semua token existing dan generate signal jika lolos threshold."""
    if settings.admin_api_key and api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    logger.info(f"Rescore triggered for chain: {chain}")
    signals_created = await ingestion.rescore_existing_tokens(chain)
    return {
        "chain": chain,
        "signals_created": signals_created,
        "timestamp": datetime.now(UTC).isoformat(),
    }
