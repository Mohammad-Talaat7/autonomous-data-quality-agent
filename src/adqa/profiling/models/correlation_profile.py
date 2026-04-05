from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CorrelationProfile:
    method: str  # "pearson" | "spearman"
    matrix: Mapping[tuple[str, str], float]
    max_abs_correlation_per_column: Mapping[str, float]
    correlation_density_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "matrix": {f"{k[0]}||{k[1]}": v for k, v in self.matrix.items()},
            "max_abs_correlation_per_column": dict(self.max_abs_correlation_per_column),
            "correlation_density_score": self.correlation_density_score,
        }
