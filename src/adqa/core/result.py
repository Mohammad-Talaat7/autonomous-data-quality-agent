# adqa/result.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from ..detection.results import DetectionResultBundle
    from ..execution.models import Action, ActionPlan
    from ..profiling.models.profiling_result import ProfilingResult
    from ..scoring.models import AggregatedScore, QualityDecision


@dataclass(frozen=True)
class ADQAResult:
    """
    Public result object returned by ADQA.analyze().
    """

    # Core outputs
    dataframe: pd.DataFrame | None

    # Phase 3
    profiles: ProfilingResult | None = None
    detections: DetectionResultBundle | None = None
    scores: AggregatedScore | None = None
    decision: QualityDecision | None = None

    # Execution semantics
    execution_mode: str | None = None
    actions: list[Action] | None = None
    blocked: bool = False

    # Human-in-the-loop
    plan: ActionPlan | None = None
    approval_payload: dict[str, Any] | None = None

    # Trace references (never raw trace data)
    trace_id: str | None = None
    config_hash: str | None = None

    # Error handling
    error: str | None = None

    def summary(self) -> str:
        """
        Generate a human-readable summary of the results.
        """
        if self.error:
            return f"❌ ADQA Error: {self.error}"

        if not self.decision:
            return "⏳ No analysis results available."

        emoji_map = {"PASS": "✅", "WARN": "⚠️"}
        status_emoji = emoji_map.get(self.decision.decision, "❌")

        lines = [
            f"{status_emoji} ADQA Quality Decision: {self.decision.decision}",
            f"   Score: {self.decision.score:.2f} (Global)",
        ]

        if self.decision.dimension_breakdown:
            worst_dim = min(
                self.decision.dimension_breakdown.items(), key=lambda x: x[1]
            )
            lines.append(f"   Worst Dimension: {worst_dim[0]} ({worst_dim[1]:.2f})")

        if self.decision.affected_columns:
            cols = ", ".join(self.decision.affected_columns[:3])
            suffix = "..." if len(self.decision.affected_columns) > 3 else ""
            lines.append(f"   Affected Columns: {cols}{suffix}")

        if self.blocked:
            lines.append("   🚫 PIPELINE BLOCKED: critical violations found.")
        elif self.approval_payload:
            lines.append("   ⏳ PENDING APPROVAL: human review required.")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result to a JSON-serializable dictionary.
        """
        return {
            "trace_id": self.trace_id,
            "decision": self.decision.to_dict() if self.decision else None,
            "score": self.decision.score if self.decision else None,
            "blocked": self.blocked,
            "execution_mode": self.execution_mode,
            "error": self.error,
            "config_hash": self.config_hash,
            "detections": self.detections.to_dict() if self.detections else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "actions": [a.to_dict() for a in self.actions] if self.actions else None,
        }

    def save_json(self, file_path: str) -> None:
        """
        Persist the result to a JSON file.
        """
        import json

        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
