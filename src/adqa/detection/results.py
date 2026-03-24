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

    column: str | None = None
    columns: list[str] | None = None

    scope: str = "column"  # column | dataset | cross_column

    severity_hint: float = 0.0  # [0, 1], NOT final severity

    metrics: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    id: str = field(default_factory=_generate_id)


# =========================
# ML Evidence (Signals Only)
# =========================


@dataclass
class MLEvidence:
    model_name: str
    signal_type: str

    column: str | None = None

    score: float = 0.0
    confidence: float = 0.0

    metadata: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=_generate_id)


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
