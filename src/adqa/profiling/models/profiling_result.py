from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .dataset_profile import DatasetProfile
from .ml_profile import MLProfile
from .risk_signal import RiskSignal


@dataclass(frozen=True)
class ProfilingResult:
    dataset_profile: DatasetProfile
    risk_signals: tuple[RiskSignal, ...]
    ml_profiles: tuple[MLProfile, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_profile": self.dataset_profile.to_dict(),
            "risk_signals": [r.to_dict() for r in self.risk_signals],
            "ml_profiles": (
                [m.to_dict() for m in self.ml_profiles] if self.ml_profiles else None
            ),
        }
