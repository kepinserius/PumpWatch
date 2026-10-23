from dataclasses import dataclass
from datetime import datetime


@dataclass
class RiskFlag:
    name: str
    status: str
    severity: str
    reason: str
    source: str
    checked_at: datetime


@dataclass
class RiskAssessment:
    token_address: str
    chain: str
    checked_at: datetime
    risk_level: str
    hard_block: bool
    flags: list[RiskFlag]
    coverage: float
    rules_version: str = "1.0"
