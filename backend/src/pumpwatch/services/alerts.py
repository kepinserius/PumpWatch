import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from pumpwatch.config import settings
from pumpwatch.domain.risk import RiskAssessment
from pumpwatch.domain.scoring import MomentumScore

logger = logging.getLogger(__name__)


class TelegramAlert:
    def __init__(self) -> None:
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.timeout = 10.0

    async def send_alert(
        self, token_address: str, chain: str, score: MomentumScore, risk: RiskAssessment
    ) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured, skipping alert")
            return False

        if risk.hard_block:
            logger.info(f"Token {token_address} blocked by risk, not sending alert")
            return False

        message = self._format_message(token_address, chain, score, risk)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                logger.info(f"Alert sent for {token_address}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def _format_message(
        self, token_address: str, chain: str, score: MomentumScore, risk: RiskAssessment
    ) -> str:
        category = self._get_category(score.total_score)
        risk_emoji = "🟢" if risk.risk_level == "low" else "🟡" if risk.risk_level == "medium" else "🔴"

        lines = [
            f"🚀 *PumpWatch Alert*",
            f"",
            f"*Token:* `{token_address[:16]}...`",
            f"*Chain:* {chain.upper()}",
            f"",
            f"*Momentum Score:* {score.total_score}/100 — {category}",
            f"*Risk Level:* {risk_emoji} {risk.risk_level.upper()}",
            f"*Data Coverage:* {score.data_coverage * 100:.0f}%",
            f"",
            f"*Top Components:*",
        ]

        sorted_components = sorted(score.components, key=lambda c: c.score * c.weight, reverse=True)[
            :3
        ]
        for comp in sorted_components:
            lines.append(f"• {comp.name.replace('_', ' ').title()}: {comp.score * 100:.0f}%")

        if risk.flags:
            failed = [f for f in risk.flags if f.status == "fail"]
            if failed:
                lines.append(f"")
                lines.append(f"⚠️ *Risk Flags:*")
                for flag in failed[:3]:
                    lines.append(f"• {flag.reason}")

        lines.append(f"")
        lines.append(f"_Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")

        return "\n".join(lines)

    def _get_category(self, score: int) -> str:
        if score >= 80:
            return "Momentum tinggi — review risiko"
        elif score >= 65:
            return "Watchlist"
        else:
            return "Belum memenuhi threshold"
