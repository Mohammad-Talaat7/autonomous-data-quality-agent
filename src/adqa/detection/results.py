# detection/results.py

import uuid
from dataclasses import dataclass, field
from typing import Any


def _generate_id() -> str:
    return str(uuid.uuid4())


# =========================
# Rule-Based Detection
# =========================


@dataclass
class DetectionResult:
    detector_name: str
    issue_type: str
    dimension: str = "unknown"

    column: str | None = None
    columns: list[str] | None = None

    scope: str = "column"  # column | dataset | cross_column

    severity_hint: float = 0.0  # [0, 1], NOT final severity
    confidence: float = 1.0  # [0, 1]

    metrics: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    id: str = field(default_factory=_generate_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "detector_name": self.detector_name,
            "issue_type": self.issue_type,
            "dimension": self.dimension,
            "column": self.column,
            "columns": self.columns,
            "scope": self.scope,
            "severity_hint": self.severity_hint,
            "confidence": self.confidence,
            "metrics": self.metrics,
            "description": self.description,
        }


# =========================
# ML Evidence (Signals Only)
# =========================


@dataclass
class MLEvidence:
    model_name: str
    signal_type: str
    dimension: str = "accuracy"

    column: str | None = None

    score: float = 0.0
    confidence: float = 1.0

    metadata: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=_generate_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "model_name": self.model_name,
            "signal_type": self.signal_type,
            "dimension": self.dimension,
            "column": self.column,
            "score": self.score,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


# =========================
# Aggregated Output
# =========================


@dataclass
class DetectionResultBundle:
    detections: list[DetectionResult] = field(default_factory=list)
    ml_evidence: list[MLEvidence] = field(default_factory=list)

    def extend(self, other: "DetectionResultBundle") -> None:
        self.detections.extend(other.detections)
        self.ml_evidence.extend(other.ml_evidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "detections": [d.to_dict() for d in self.detections],
            "ml_evidence": [e.to_dict() for e in self.ml_evidence],
        }
