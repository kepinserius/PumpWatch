from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ScoreComponent:
    name: str
    score: float
    weight: float
    details: dict[str, Any]


@dataclass
class MomentumScore:
    token_address: str
    chain: str
    calculated_at: datetime
    total_score: int
    components: list[ScoreComponent]
    features: dict[str, Any]
    data_coverage: float
    rules_version: str = "1.0"
