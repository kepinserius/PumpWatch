from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pumpwatch.domain.alerts import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertRuleList,
    CooldownResponse,
)
from pumpwatch.services.alert_manager import AlertManager

router = APIRouter()


@router.post("/alert-rules", response_model=AlertRuleResponse)
async def create_alert_rule(rule: AlertRuleCreate) -> dict:
    """Create new alert rule."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    manager = AlertManager(db)
    rule_id = await manager.create_alert_rule(rule)

    created = await manager.get_alert_rule(rule_id)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create rule")

    return {
        "id": created["id"],
        "name": created["name"],
        "token_id": created["token_id"],
        "is_global": created["is_global"],
        "momentum_threshold": float(created["momentum_threshold"]) if created["momentum_threshold"] else None,
        "risk_level_max": created["risk_level_max"],
        "min_liquidity_usd": float(created["min_liquidity_usd"]) if created["min_liquidity_usd"] else None,
        "cooldown_minutes": created["cooldown_minutes"],
        "priority": created["priority"],
        "enabled": created["enabled"],
        "created_at": created["created_at"].isoformat(),
    }


@router.get("/alert-rules", response_model=AlertRuleList)
async def list_alert_rules(token_id: int | None = None, limit: int = 50, offset: int = 0) -> dict:
    """List alert rules. Filter by token_id if provided."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    manager = AlertManager(db)
    rules = await manager.list_alert_rules(token_id, limit, offset)

    items = [
        {
            "id": r["id"],
            "name": r["name"],
            "token_id": r["token_id"],
            "is_global": r["is_global"],
            "momentum_threshold": float(r["momentum_threshold"]) if r["momentum_threshold"] else None,
            "risk_level_max": r["risk_level_max"],
            "min_liquidity_usd": float(r["min_liquidity_usd"]) if r["min_liquidity_usd"] else None,
            "cooldown_minutes": r["cooldown_minutes"],
            "priority": r["priority"],
            "enabled": r["enabled"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rules
    ]

    return {"total": len(items), "items": items}


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(rule_id: int) -> dict:
    """Get single alert rule by ID."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    manager = AlertManager(db)
    rule = await manager.get_alert_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    return {
        "id": rule["id"],
        "name": rule["name"],
        "token_id": rule["token_id"],
        "is_global": rule["is_global"],
        "momentum_threshold": float(rule["momentum_threshold"]) if rule["momentum_threshold"] else None,
        "risk_level_max": rule["risk_level_max"],
        "min_liquidity_usd": float(rule["min_liquidity_usd"]) if rule["min_liquidity_usd"] else None,
        "cooldown_minutes": rule["cooldown_minutes"],
        "priority": rule["priority"],
        "enabled": rule["enabled"],
        "created_at": rule["created_at"].isoformat(),
    }


@router.patch("/alert-rules/{rule_id}")
async def update_alert_rule(rule_id: int, updates: AlertRuleUpdate) -> dict:
    """Update alert rule."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    manager = AlertManager(db)
    updated = await manager.update_alert_rule(rule_id, updates)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found or no changes")

    return {"status": "updated", "rule_id": rule_id}


@router.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(rule_id: int) -> dict:
    """Delete alert rule."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    manager = AlertManager(db)
    deleted = await manager.delete_alert_rule(rule_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    return {"status": "deleted", "rule_id": rule_id}


@router.get("/alert-rules/{rule_id}/cooldowns", response_model=list[CooldownResponse])
async def get_rule_cooldowns(rule_id: int) -> list[dict]:
    """List active cooldowns for specific rule."""
    from pumpwatch.main import db

    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    manager = AlertManager(db)
    cooldowns = await manager.get_active_cooldowns(rule_id)

    return [
        {
            "id": c["id"],
            "token_id": c["token_id"],
            "pool_id": c["pool_id"],
            "alert_rule_id": c["alert_rule_id"],
            "last_alert_sent_at": c["last_alert_sent_at"].isoformat(),
            "next_alert_allowed_at": c["next_alert_allowed_at"].isoformat(),
            "created_at": c["created_at"].isoformat(),
        }
        for c in cooldowns
    ]
