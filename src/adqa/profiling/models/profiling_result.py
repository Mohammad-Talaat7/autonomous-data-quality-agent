from __future__ import annotations

from dataclasses import dataclass

from .dataset_profile import DatasetProfile
from .ml_profile import MLProfile
from .risk_signal import RiskSignal


@dataclass(frozen=True)
class ProfilingResult:
    dataset_profile: DatasetProfile
    risk_signals: tuple[RiskSignal, ...]
    ml_profiles: tuple[MLProfile, ...] | None = None
