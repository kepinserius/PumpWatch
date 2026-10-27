import logging
from datetime import UTC, datetime, timedelta

from pumpwatch.database import Database
from pumpwatch.services.analytics import AnalyticsService
from pumpwatch.config import settings

logger = logging.getLogger(__name__)


async def _background_analytics() -> None:
    """
    Loop background yang compute analytics aggregates secara periodik.
    """
    interval = settings.analytics_aggregation_interval_minutes * 60

    if interval <= 0:
        logger.info("Background analytics: ANALYTICS_AGGREGATION_INTERVAL=0, aggregation dinonaktifkan")
        return

    logger.info(f"Background analytics: akan compute aggregates setiap {settings.analytics_aggregation_interval_minutes} menit")
    await asyncio.sleep(interval)

    from pumpwatch.main import db

    if not db.pool:
        logger.warning("Background analytics: Database not connected, skipping")
        return

    analytics = AnalyticsService(db)

    while True:
        logger.info("Background analytics: memulai aggregation...")
        try:
            for timeframe in ['1h', '4h', '24h']:
                await analytics.compute_aggregates(timeframe)
            logger.info("Analytics aggregation selesai, next in 1h")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Analytics aggregation error (akan retry di interval berikutnya): {e}")

        await asyncio.sleep(interval)
