from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    token_id: int | None = None
    is_global: bool = False
    momentum_threshold: float | None = None
    risk_level_max: str | None = None
    min_liquidity_usd: float | None = None
    cooldown_minutes: int = Field(default=60, ge=1, le=1440)
    priority: Priority = Priority.NORMAL
    enabled: bool = True


class AlertRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    momentum_threshold: float | None = None
    risk_level_max: str | None = None
    min_liquidity_usd: float | None = None
    cooldown_minutes: int | None = Field(default=None, ge=1, le=1440)
    priority: Priority | None = None
    enabled: bool | None = None


class AlertRule(BaseModel):
    id: int
    name: str
    token_id: int | None
    is_global: bool
    momentum_threshold: float | None
    risk_level_max: str | None
    min_liquidity_usd: float | None
    cooldown_minutes: int
    priority: str
    enabled: bool
    created_at: str
    updated_at: str


class AlertRuleResponse(BaseModel):
    id: int
    name: str
    token_id: int | None
    is_global: bool
    momentum_threshold: float | None
    risk_level_max: str | None
    min_liquidity_usd: float | None
    cooldown_minutes: int
    priority: str
    enabled: bool
    created_at: str


class CooldownResponse(BaseModel):
    id: int
    token_id: int
    pool_id: int | None
    alert_rule_id: int
    last_alert_sent_at: str
    next_alert_allowed_at: str
    created_at: str


class AlertRuleList(BaseModel):
    total: int
    items: list[AlertRuleResponse]