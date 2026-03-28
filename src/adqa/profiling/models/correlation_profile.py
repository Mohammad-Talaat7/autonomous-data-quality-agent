from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class CorrelationProfile:
    method: str  # "pearson" | "spearman"
    matrix: Mapping[tuple[str, str], float]
    max_abs_correlation_per_column: Mapping[str, float]
    correlation_density_score: float
