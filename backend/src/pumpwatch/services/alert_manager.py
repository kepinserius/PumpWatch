import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from pumpwatch.database import Database
from pumpwatch.domain.alerts import AlertRule, AlertRuleCreate, AlertRuleUpdate
from pumpwatch.domain.risk import RiskAssessment
from pumpwatch.domain.scoring import MomentumScore

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self, db: Database):
        self.db = db

    async def create_alert_rule(self, rule: AlertRuleCreate) -> int:
        """Create new alert rule. Return rule_id."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO alert_rules 
                (name, token_id, is_global, momentum_threshold, risk_level_max, 
                 min_liquidity_usd, cooldown_minutes, priority, enabled)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                rule.name,
                rule.token_id,
                rule.is_global,
                rule.momentum_threshold,
                rule.risk_level_max,
                rule.min_liquidity_usd,
                rule.cooldown_minutes,
                rule.priority.value,
                rule.enabled,
            )
            return row["id"]

    async def update_alert_rule(self, rule_id: int, updates: AlertRuleUpdate) -> bool:
        """Update existing alert rule. Return True if updated."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        update_fields = []
        values = []
        param_count = 1

        if updates.name is not None:
            update_fields.append(f"name = ${param_count}")
            values.append(updates.name)
            param_count += 1

        if updates.momentum_threshold is not None:
            update_fields.append(f"momentum_threshold = ${param_count}")
            values.append(updates.momentum_threshold)
            param_count += 1

        if updates.risk_level_max is not None:
            update_fields.append(f"risk_level_max = ${param_count}")
            values.append(updates.risk_level_max)
            param_count += 1

        if updates.min_liquidity_usd is not None:
            update_fields.append(f"min_liquidity_usd = ${param_count}")
            values.append(updates.min_liquidity_usd)
            param_count += 1

        if updates.cooldown_minutes is not None:
            update_fields.append(f"cooldown_minutes = ${param_count}")
            values.append(updates.cooldown_minutes)
            param_count += 1

        if updates.priority is not None:
            update_fields.append(f"priority = ${param_count}")
            values.append(updates.priority.value)
            param_count += 1

        if updates.enabled is not None:
            update_fields.append(f"enabled = ${param_count}")
            values.append(updates.enabled)
            param_count += 1

        if not update_fields:
            return False

        update_fields.append("updated_at = NOW()")
        values.append(rule_id)

        query = f"""
            UPDATE alert_rules 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
        """

        async with self.db.pool.acquire() as conn:
            result = await conn.execute(query, *values)
            return result.split()[-1] != "0"

    async def delete_alert_rule(self, rule_id: int) -> bool:
        """Delete alert rule. Return True if deleted."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        async with self.db.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM alert_rules WHERE id = $1",
                rule_id,
            )
            return result.split()[-1] != "0"

    async def get_alert_rule(self, rule_id: int) -> dict | None:
        """Get single alert rule by ID."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM alert_rules WHERE id = $1",
                rule_id,
            )
            return dict(row) if row else None

    async def list_alert_rules(
        self, token_id: int | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """List alert rules. Filter by token_id if provided."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        async with self.db.pool.acquire() as conn:
            if token_id is not None:
                rows = await conn.fetch(
                    """
                    SELECT * FROM alert_rules 
                    WHERE token_id = $1 OR is_global = true
                    ORDER BY priority DESC, created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    token_id,
                    limit,
                    offset,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM alert_rules 
                    ORDER BY priority DESC, created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )

            return [dict(row) for row in rows]

    async def check_alert_conditions(
        self,
        token_id: int,
        pool_id: int | None,
        score: MomentumScore,
        risk: RiskAssessment,
    ) -> list[dict]:
        """
        Check which alert rules are triggered untuk token ini.
        Return list of triggered rules (sorted by priority).
        """
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM alert_rules 
                WHERE (token_id = $1 OR is_global = true)
                AND enabled = true
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'normal' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    created_at DESC
                """,
                token_id,
            )

        triggered = []
        for row in rows:
            rule = dict(row)

            if not self._rule_matches(rule, score, risk):
                continue

            triggered.append(rule)

        return triggered

    def _rule_matches(
        self, rule: dict, score: MomentumScore, risk: RiskAssessment
    ) -> bool:
        """Check if rule conditions match current score/risk."""

        if rule["momentum_threshold"] is not None:
            if score.total_score < float(rule["momentum_threshold"]):
                return False

        if rule["risk_level_max"] is not None:
            risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            current_level = risk_order.get(risk.risk_level, 3)
            max_level = risk_order.get(rule["risk_level_max"], 3)
            if current_level > max_level:
                return False

        if rule["min_liquidity_usd"] is not None:
            if not hasattr(score, "features") or not score.features:
                return False
            liquidity = score.features.get("liquidity_usd")
            if liquidity is None or float(liquidity) < float(rule["min_liquidity_usd"]):
                return False

        return True

    async def should_send_alert(
        self, token_id: int, pool_id: int | None, rule: dict
    ) -> bool:
        """Check if alert dapat dikirim (cooldown check)."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        now = datetime.now(UTC)

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT next_alert_allowed_at 
                FROM alert_cooldowns 
                WHERE token_id = $1 
                AND pool_id IS NOT DISTINCT FROM $2
                AND alert_rule_id = $3
                """,
                token_id,
                pool_id,
                rule["id"],
            )

            if not row:
                return True

            next_allowed = row["next_alert_allowed_at"]
            return now >= next_allowed

    async def record_alert_sent(
        self, token_id: int, pool_id: int | None, rule: dict
    ):
        """Record alert sent, update cooldown."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        now = datetime.now(UTC)
        next_allowed = now + timedelta(minutes=rule["cooldown_minutes"])

        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO alert_cooldowns 
                (token_id, pool_id, alert_rule_id, last_alert_sent_at, next_alert_allowed_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (token_id, pool_id, alert_rule_id)
                DO UPDATE SET 
                    last_alert_sent_at = EXCLUDED.last_alert_sent_at,
                    next_alert_allowed_at = EXCLUDED.next_alert_allowed_at
                """,
                token_id,
                pool_id,
                rule["id"],
                now,
                next_allowed,
            )

    async def get_active_cooldowns(self, rule_id: int | None = None) -> list[dict]:
        """Get active cooldowns. Filter by rule_id if provided."""
        if not self.db.pool:
            raise RuntimeError("Database not connected")

        now = datetime.now(UTC)

        async with self.db.pool.acquire() as conn:
            if rule_id is not None:
                rows = await conn.fetch(
                    """
                    SELECT * FROM alert_cooldowns 
                    WHERE alert_rule_id = $1 
                    AND next_alert_allowed_at > $2
                    ORDER BY next_alert_allowed_at ASC
                    """,
                    rule_id,
                    now,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM alert_cooldowns 
                    WHERE next_alert_allowed_at > $1
                    ORDER BY next_alert_allowed_at ASC
                    """,
                    now,
                )

            return [dict(row) for row in rows]
