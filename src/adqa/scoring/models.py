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

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector_id": self.detector_id,
            "rule_id": self.rule_id,
            "issue_type": self.issue_type,
            "dimension": self.dimension,
            "column": self.column,
            "severity": self.severity,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector_id": self.detector_id,
            "rule_id": self.rule_id,
            "issue_type": self.issue_type,
            "dimension": self.dimension,
            "column": self.column,
            "severity": self.severity,
            "confidence": self.confidence,
            "weight": self.weight,
            "final_score": self.final_score,
            "metadata": self.metadata,
        }


# ---------- AGGREGATION ----------


@dataclass
class AggregatedScore:
    global_score: float

    issue_breakdown: dict[str, float]
    column_breakdown: dict[str, float]
    dimension_breakdown: dict[str, float]

    raw_scores: list[Score]

    def to_dict(self) -> dict[str, Any]:
        return {
            "global_score": self.global_score,
            "issue_breakdown": self.issue_breakdown,
            "column_breakdown": self.column_breakdown,
            "dimension_breakdown": self.dimension_breakdown,
            "raw_scores": [s.to_dict() for s in self.raw_scores],
        }


# ---------- DECISION ----------


@dataclass
class QualityDecision:
    decision: str  # PASS / WARN / FAIL
    score: float

    severity_level: str

    breakdown: dict[str, float]
    dimension_breakdown: dict[str, float]
    column_breakdown: dict[str, float]
    issue_map: dict[str, list[str]]
    dominant_issues: list[str]
    affected_columns: list[str]

    thresholds_used: dict[str, float]

    explanation: str
    issue_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "score": self.score,
            "severity_level": self.severity_level,
            "breakdown": self.breakdown,
            "dimension_breakdown": self.dimension_breakdown,
            "column_breakdown": self.column_breakdown,
            "issue_map": self.issue_map,
            "dominant_issues": self.dominant_issues,
            "affected_columns": self.affected_columns,
            "thresholds_used": self.thresholds_used,
            "explanation": self.explanation,
            "issue_metadata": self.issue_metadata,
        }


@dataclass
class ScoringResult:
    aggregated: AggregatedScore
    decision: QualityDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "aggregated": self.aggregated.to_dict(),
            "decision": self.decision.to_dict(),
        }
