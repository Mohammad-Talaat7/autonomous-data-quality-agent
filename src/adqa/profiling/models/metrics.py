from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

# =========================
# Structural Metrics
# =========================


@dataclass(frozen=True)
class StructuralMetrics:
    null_ratio: float
    unique_ratio: float
    duplicate_ratio: float
    memory_usage_bytes: int


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


# =========================
# Datetime Metrics
# =========================


@dataclass(frozen=True)
class DatetimeMetrics:
    min: str  # ISO formatted
    max: str
    range_days: float
    monotonic: bool


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


# =========================
# Behavioral Metrics
# =========================


@dataclass(frozen=True)
class BehavioralMetrics:
    outlier_ratio: float
    heavy_tail_score: float
    multimodality_score: float
    low_variance_indicator: float
