# adqa/trace/reasoning.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID, uuid4

from .enums import (
    ReasoningTraceEventDict,
    TraceComponent,
    TraceEventType,
    TraceSeverity,
    TraceValue,
)
from .events import TraceEvent


class ReasonCode(str):
    """
    Stable, deterministic reason codes.
    These MUST NOT be free text.
    """

    HIGH_NULL_RATIO: str = "high_null_ratio"
    LOW_CARDINALITY: str = "low_cardinality"
    OUTLIER_DETECTED: str = "outlier_detected"
    RULE_VIOLATION: str = "rule_violation"
    METRIC_THRESHOLD_EXCEEDED: str = "metric_threshold_exceeded"
    CRITICAL_COLUMN: str = "critical_column"
    MISSING_VALUES: str = "missing_values"
    DUPLICATE_ROWS: str = "duplicate_rows"
    CONSTANT_COLUMN: str = "constant_column"
    OUTLIERS: str = "outliers"
    HIGH_SKEWNESS: str = "high_skewness"
    HIGH_CORRELATION: str = "high_correlation"
    RANGE_VIOLATION: str = "range_violation"
    PATTERN_VIOLATION: str = "pattern_violation"
    PII_DETECTED: str = "pii_detected"
    ANOMALY_SCORE: str = "anomaly_score"


DETECTION_REASON_CODE_MAP: dict[str, str] = {
    "missing_values": ReasonCode.MISSING_VALUES,
    "duplicate_rows": ReasonCode.DUPLICATE_ROWS,
    "constant_column": ReasonCode.CONSTANT_COLUMN,
    "outliers": ReasonCode.OUTLIERS,
    "high_skewness": ReasonCode.HIGH_SKEWNESS,
    "high_correlation": ReasonCode.HIGH_CORRELATION,
    "range_violation": ReasonCode.RANGE_VIOLATION,
    "pattern_violation": ReasonCode.PATTERN_VIOLATION,
    "pii_detected": ReasonCode.PII_DETECTED,
    "anomaly_score": ReasonCode.ANOMALY_SCORE,
}

ML_REASON_CODE_MAP: dict[str, str] = {
    "pii_detected": ReasonCode.PII_DETECTED,
    "anomaly_score": ReasonCode.ANOMALY_SCORE,
}


def reason_code_for_issue(issue_type: str) -> str:
    return DETECTION_REASON_CODE_MAP.get(issue_type, ReasonCode.RULE_VIOLATION)


def collect_reason_codes(bundle: object | None) -> list[str]:
    if bundle is None:
        return []

    seen: set[str] = set()
    ordered: list[str] = []

    detections = getattr(bundle, "detections", ())
    for detection in detections:
        code = reason_code_for_issue(getattr(detection, "issue_type", ""))
        if code not in seen:
            seen.add(code)
            ordered.append(code)

    ml_evidence = getattr(bundle, "ml_evidence", ())
    for evidence in ml_evidence:
        code = ML_REASON_CODE_MAP.get(
            getattr(evidence, "signal_type", ""),
            ReasonCode.METRIC_THRESHOLD_EXCEEDED,
        )
        if code not in seen:
            seen.add(code)
            ordered.append(code)

    return ordered


@dataclass
class ReasoningTraceEvent(TraceEvent):
    """
    TraceEvent representing a deterministic decision reasoning.

    This event explains WHY a decision was made, not WHAT was executed.
    """

    # Required linkage to execution
    execution_event_id: UUID = field(default_factory=uuid4)

    # Decision quality
    confidence: float = 0.0

    # Deterministic reasons
    reasons: list[str] = field(default_factory=list)

    # Optional metric evidence
    evidence: dict[str, TraceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Enforce correct trace classification
        self.component: TraceComponent = TraceComponent.TRACE
        self.event_type: TraceEventType = TraceEventType.DECISION
        self.severity: TraceSeverity = TraceSeverity.INFO

        # Validate confidence
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        # Enforce reproducibility
        if not self.reasons:
            raise ValueError(
                "ReasoningTraceEvent must include at least one reason code"
            )

    @override
    def to_dict(self) -> ReasoningTraceEventDict:
        base = super().to_dict()
        from .hooks.serialize import to_trace_value

        return {
            **base,
            "execution_event_id": str(self.execution_event_id),
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "evidence": {k: to_trace_value(v) for k, v in self.evidence.items()},
        }
