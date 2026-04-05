from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RiskSignalType(StrEnum):
    NULL_RATIO = "null_ratio"
    UNIQUE_RATIO = "unique_ratio"
    DUPLICATE_RATIO = "duplicate_ratio"
    CONSTANT_COLUMN = "constant_column"
    LOW_VARIANCE = "low_variance"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"
    OUTLIER_RATIO = "outlier_ratio"
    HEAVY_TAIL = "heavy_tail"
    MULTIMODALITY = "multimodality"
    HIGH_CARDINALITY = "high_cardinality"
    DOMINANCE_RATIO = "dominance_ratio"
    CORRELATION = "correlation"
    CORRELATION_DENSITY = "correlation_density"
    IDENTIFIER_LIKELIHOOD = "identifier_likelihood"


@dataclass(frozen=True)
class RiskSignal:
    type: RiskSignalType
    subject: str  # column name or "dataset"
    value: float | bool | str
    metadata: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "subject": self.subject,
            "value": self.value,
            "metadata": dict(self.metadata) if self.metadata else None,
        }
