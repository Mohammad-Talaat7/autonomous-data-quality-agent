# src/adqa/trace/reasoning.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing_extensions import override
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

        return {
            **base,
            "execution_event_id": str(self.execution_event_id),
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "evidence": self.evidence,
        }
