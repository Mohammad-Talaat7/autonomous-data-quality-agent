from dataclasses import dataclass, field
from typing import Any

# ---------- INPUT ----------


@dataclass
class NormalizedDetection:
    detector_id: str
    rule_id: str
    issue_type: str
    dimension: str  # completeness, validity, etc.

    column: str | None

    severity: float  # [0, 1]
    confidence: float  # [0, 1]

    metadata: dict[str, Any] = field(default_factory=dict)


# ---------- SCORE ----------


@dataclass
class Score:
    detector_id: str
    rule_id: str
    issue_type: str
    dimension: str
    column: str | None

    severity: float
    confidence: float
    weight: float

    final_score: float

    metadata: dict[str, Any] = field(default_factory=dict)


# ---------- AGGREGATION ----------


@dataclass
class AggregatedScore:
    global_score: float

    issue_breakdown: dict[str, float]
    column_breakdown: dict[str, float]
    dimension_breakdown: dict[str, float]

    raw_scores: list[Score]


# ---------- DECISION ----------


@dataclass
class QualityDecision:
    decision: str  # PASS / WARN / FAIL
    score: float

    severity_level: str

    breakdown: dict[str, float]
    dimension_breakdown: dict[str, float]
    dominant_issues: list[str]
    affected_columns: list[str]

    thresholds_used: dict[str, float]

    explanation: str
