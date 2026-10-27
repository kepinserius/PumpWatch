from fastapi import APIRouter, HTTPException

from pumpwatch.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/analytics/momentum/trend")
async def get_momentum_trend(timeframe: str = '1h', hours: int = 24) -> list[dict]:
    """Momentum trend time-series."""
    if timeframe not in ['1h', '4h', '24h']:
        raise HTTPException(status_code=400, detail="Invalid timeframe. Must be 1h, 4h, or 24h")
    
    if hours <= 0 or hours > 720:
        raise HTTPException(status_code=400, detail="hours must be between 1 and 720")

    from pumpwatch.main import db
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    analytics = AnalyticsService(db)
    return await analytics.get_momentum_trend(timeframe, hours)


@router.get("/analytics/risk/trend")
async def get_risk_trend(timeframe: str = '1h', hours: int = 24) -> list[dict]:
    """Risk distribution trend."""
    if timeframe not in ['1h', '4h', '24h']:
        raise HTTPException(status_code=400, detail="Invalid timeframe. Must be 1h, 4h, or 24h")
    
    if hours <= 0 or hours > 720:
        raise HTTPException(status_code=400, detail="hours must be between 1 and 720")

    from pumpwatch.main import db
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    analytics = AnalyticsService(db)
    return await analytics.get_risk_trend(timeframe, hours)


@router.get("/analytics/top-tokens")
async def get_top_tokens(category: str, limit: int = 10) -> list[dict]:
    """Top tokens per kategori."""
    valid_categories = ['high_momentum', 'watchlist', 'high_liquidity', 'new_pools']
    if category not in valid_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    if limit <= 0 or limit > 50:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 50")

    from pumpwatch.main import db
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    analytics = AnalyticsService(db)
    return await analytics.get_top_tokens(category, limit)


@router.get("/analytics/overview")
async def get_analytics_overview() -> dict:
    """
    Dashboard overview:
    - Total scanned last 24h
    - Avg momentum score
    - Risk distribution
    """
    from pumpwatch.main import db
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    analytics = AnalyticsService(db)
    return await analytics.get_overview()
