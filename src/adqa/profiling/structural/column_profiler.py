from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..behavioral.behavioral_profiler import compute_behavioral_metrics
from ..models.column_profile import ColumnProfile, LogicalType
from ..models.metrics import (
    CategoricalMetrics,
    DatetimeMetrics,
    NumericMetrics,
    StructuralMetrics,
    TextMetrics,
)
from .logical_type_inference import infer_logical_type
from .summary import ColumnSummary, build_column_summary

# =========================
# Utility Pure Functions
# =========================


def compute_structural_metrics(summary: ColumnSummary) -> StructuralMetrics:
    return StructuralMetrics(
        null_ratio=summary.null_ratio,
        unique_ratio=(
            summary.unique_count / summary.total_count
            if summary.total_count > 0
            else 0.0
        ),
        duplicate_ratio=(
            (summary.total_count - summary.unique_count) / summary.total_count
            if summary.total_count > 0
            else 0.0
        ),
        memory_usage_bytes=summary.memory_usage,
    )


# =========================
# Numeric Metrics
# =========================


def compute_numeric_metrics(summary: ColumnSummary) -> NumericMetrics:
    clean = summary.clean_series
    if clean.empty:
        return NumericMetrics(
            mean=0.0,
            median=0.0,
            std=0.0,
            variance=0.0,
            min=0.0,
            max=0.0,
            quantiles={},
            iqr=0.0,
            skewness=0.0,
            kurtosis=0.0,
            bimodality_coefficient=0.0,
            zero_ratio=0.0,
            coefficient_of_variation=0.0,
        )

    # Single pass for most statistics
    stats = clean.agg(["mean", "std", "var", "min", "max", "skew", "kurt", "median"])

    quantiles = clean.quantile([0.25, 0.75]).to_dict()
    iqr = quantiles[0.75] - quantiles[0.25]

    all_quantiles = {
        0.25: quantiles[0.25],
        0.5: float(stats["median"]),
        0.75: quantiles[0.75],
    }

    mean = float(stats["mean"])
    std = float(stats["std"])
    kurtosis = float(stats["kurt"])
    skewness = float(stats["skew"])
    n = len(clean)

    # Sarle's Bimodality Coefficient
    if n > 3:
        numerator = (skewness**2) + 1
        denominator = kurtosis + 3 + ((3 * (n - 1) ** 2) / ((n - 2) * (n - 3)))
        bimodality_coefficient = (
            float(min(numerator / denominator, 1.0)) if denominator != 0 else 0.0
        )
    else:
        bimodality_coefficient = 0.0

    return NumericMetrics(
        mean=mean,
        median=float(stats["median"]),
        std=std,
        variance=float(stats["var"]),
        min=float(stats["min"]),
        max=float(stats["max"]),
        quantiles=all_quantiles,
        iqr=float(iqr),
        skewness=skewness,
        kurtosis=kurtosis,
        bimodality_coefficient=bimodality_coefficient,
        zero_ratio=float((clean == 0).sum() / len(clean)),
        coefficient_of_variation=float(std / mean) if mean != 0 else 0.0,
    )


# =========================
# Categorical Metrics
# =========================


def compute_categorical_metrics(
    summary: ColumnSummary, thresholds: ProfilingThresholds | None = None
) -> CategoricalMetrics:
    clean = summary.clean_series
    total = summary.clean_count

    rare_threshold = thresholds.rare_category_threshold if thresholds else 0.01

    if total == 0:
        return CategoricalMetrics(
            cardinality=0,
            entropy=0.0,
            mode=None,
            mode_ratio=0.0,
            dominance_ratio=0.0,
            rare_categories=[],
        )

    # Use pre-calculated value_counts if available
    value_counts = (
        summary.value_counts
        if summary.value_counts is not None
        else clean.value_counts()
    )

    probabilities = value_counts / total
    entropy = -np.sum(probabilities * np.log2(probabilities))

    mode = value_counts.index[0]
    mode_ratio = value_counts.iloc[0] / total

    # Identify rare categories
    rare_categories = (
        value_counts[probabilities < rare_threshold].index.astype(str).tolist()
    )

    return CategoricalMetrics(
        cardinality=int(summary.unique_count),
        entropy=float(entropy),
        mode=str(mode),
        mode_ratio=float(mode_ratio),
        dominance_ratio=float(mode_ratio),
        rare_categories=rare_categories,
    )


# =========================
# Datetime Metrics
# =========================


def compute_datetime_metrics(summary: ColumnSummary) -> DatetimeMetrics:
    clean = summary.clean_series
    if clean.empty:
        return DatetimeMetrics(
            min="",
            max="",
            range_days=0.0,
            monotonic=False,
        )

    min_val = clean.min()
    max_val = clean.max()

    range_days = (max_val - min_val).total_seconds() / 86400

    return DatetimeMetrics(
        min=min_val.isoformat(),
        max=max_val.isoformat(),
        range_days=float(range_days),
        monotonic=clean.is_monotonic_increasing,
    )


# =========================
# Text Metrics
# =========================


def compute_text_metrics(summary: ColumnSummary) -> TextMetrics:
    clean = summary.clean_series.astype(str)
    total = summary.clean_count

    if total == 0:
        return TextMetrics(
            avg_length=0.0,
            length_std=0.0,
            digit_ratio=0.0,
            whitespace_ratio=0.0,
            special_char_ratio=0.0,
        )

    lengths = clean.str.len()

    total_chars = lengths.sum()
    digit_count = clean.str.count(r"\d").sum()
    whitespace_count = clean.str.count(r"\s").sum()
    special_count = clean.str.count(r"[^\w\s]").sum()

    return TextMetrics(
        avg_length=float(lengths.mean()),
        length_std=float(lengths.std()),
        digit_ratio=float(digit_count / total_chars) if total_chars else 0.0,
        whitespace_ratio=float(whitespace_count / total_chars) if total_chars else 0.0,
        special_char_ratio=float(special_count / total_chars) if total_chars else 0.0,
    )


# =========================
# Column Profiling
# =========================


def profile_column(
    series: pd.Series[Any], thresholds: ProfilingThresholds | None = None
) -> ColumnProfile:
    # First pass: build summary
    summary = build_column_summary(series, compute_counts=False, thresholds=thresholds)
    logical_type = infer_logical_type(summary, thresholds=thresholds)

    # If categorical, we might want to rebuild summary with value_counts
    if logical_type == LogicalType.CATEGORICAL:
        summary = build_column_summary(
            series, compute_counts=True, thresholds=thresholds
        )

    structural_metrics = compute_structural_metrics(summary)
    behavioral_metrics = compute_behavioral_metrics(
        summary, logical_type, thresholds=thresholds
    )

    numeric_metrics = None
    categorical_metrics = None
    datetime_metrics = None
    text_metrics = None

    if logical_type == LogicalType.NUMERIC:
        numeric_metrics = compute_numeric_metrics(summary)

    elif logical_type == LogicalType.CATEGORICAL:
        categorical_metrics = compute_categorical_metrics(
            summary, thresholds=thresholds
        )

    elif logical_type == LogicalType.DATETIME:
        datetime_metrics = compute_datetime_metrics(summary)

    elif logical_type == LogicalType.TEXT:
        text_metrics = compute_text_metrics(summary)

    return ColumnProfile(
        name=str(series.name),
        dtype=str(series.dtype),
        logical_type=logical_type,
        structural_metrics=structural_metrics,
        behavioral_metrics=behavioral_metrics,
        numeric_metrics=numeric_metrics,
        categorical_metrics=categorical_metrics,
        datetime_metrics=datetime_metrics,
        text_metrics=text_metrics,
    )
