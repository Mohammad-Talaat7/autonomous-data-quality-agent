from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

# =========================
# Structural Metrics
# =========================


@dataclass(frozen=True)
class StructuralMetrics:
    null_ratio: float
    unique_ratio: float
    duplicate_ratio: float
    memory_usage_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "null_ratio": self.null_ratio,
            "unique_ratio": self.unique_ratio,
            "duplicate_ratio": self.duplicate_ratio,
            "memory_usage_bytes": self.memory_usage_bytes,
        }


# =========================
# Numeric Metrics
# =========================


@dataclass(frozen=True)
class NumericMetrics:
    mean: float
    median: float
    std: float
    variance: float
    min: float
    max: float
    quantiles: Mapping[float, float]
    iqr: float
    skewness: float
    kurtosis: float
    bimodality_coefficient: float
    zero_ratio: float
    coefficient_of_variation: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "variance": self.variance,
            "min": self.min,
            "max": self.max,
            "quantiles": dict(self.quantiles),
            "iqr": self.iqr,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "bimodality_coefficient": self.bimodality_coefficient,
            "zero_ratio": self.zero_ratio,
            "coefficient_of_variation": self.coefficient_of_variation,
        }


# =========================
# Categorical Metrics
# =========================


@dataclass(frozen=True)
class CategoricalMetrics:
    cardinality: int
    entropy: float
    mode: str | None
    mode_ratio: float
    dominance_ratio: float
    rare_categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cardinality": self.cardinality,
            "entropy": self.entropy,
            "mode": self.mode,
            "mode_ratio": self.mode_ratio,
            "dominance_ratio": self.dominance_ratio,
            "rare_categories": self.rare_categories,
        }


# =========================
# Datetime Metrics
# =========================


@dataclass(frozen=True)
class DatetimeMetrics:
    min: str  # ISO formatted
    max: str
    range_days: float
    monotonic: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "min": self.min,
            "max": self.max,
            "range_days": self.range_days,
            "monotonic": self.monotonic,
        }


# =========================
# Text Metrics
# =========================


@dataclass(frozen=True)
class TextMetrics:
    avg_length: float
    length_std: float
    digit_ratio: float
    whitespace_ratio: float
    special_char_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "avg_length": self.avg_length,
            "length_std": self.length_std,
            "digit_ratio": self.digit_ratio,
            "whitespace_ratio": self.whitespace_ratio,
            "special_char_ratio": self.special_char_ratio,
        }


# =========================
# Behavioral Metrics
# =========================


@dataclass(frozen=True)
class BehavioralMetrics:
    outlier_ratio: float
    heavy_tail_score: float
    multimodality_score: float
    low_variance_indicator: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "outlier_ratio": self.outlier_ratio,
            "heavy_tail_score": self.heavy_tail_score,
            "multimodality_score": self.multimodality_score,
            "low_variance_indicator": self.low_variance_indicator,
        }
