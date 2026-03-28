from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..models.metrics import BehavioralMetrics
from ..structural.summary import ColumnSummary


def compute_numeric_behavior(
    summary: ColumnSummary, thresholds: ProfilingThresholds | None = None
) -> BehavioralMetrics | None:
    clean = summary.clean_series

    # Thresholds
    min_rows = thresholds.min_rows_numeric_behavior if thresholds else 5
    iqr_mult = thresholds.outlier_iqr_multiplier if thresholds else 1.5

    if len(clean) < min_rows:
        return None

    kurtosis = cast(float, clean.kurt())
    skewness = cast(float, clean.skew())
    n = len(clean)

    # 1. Outlier Detection (Adaptive)
    # Use Z-score for roughly normal data, IQR for skewed data
    if abs(skewness) < 1.0:
        # Z-score method
        mean = clean.mean()
        std = clean.std()
        if std == 0:
            outlier_ratio = 0.0
        else:
            z_scores = (clean - mean).abs() / std
            outlier_ratio = float((z_scores > 3.0).sum() / n)
    else:
        # IQR method
        q1 = clean.quantile(0.25)
        q3 = clean.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            outlier_ratio = 0.0
        else:
            lower = q1 - iqr_mult * iqr
            upper = q3 + iqr_mult * iqr
            outlier_ratio = float(((clean < lower) | (clean > upper)).sum() / n)

    # 2. Sarle's Bimodality Coefficient (b)
    # b = (skewness^2 + 1) / (kurtosis + 3 * ((n-1)^2 / ((n-2)*(n-3))))
    # For large n, b = (skewness^2 + 1) / (kurtosis + 3)
    # kurtosis here is excess kurtosis (pandas default)

    if n > 3:
        numerator = (skewness**2) + 1
        # Adding 3 to excess kurtosis gives the Pearson kurtosis
        denominator = kurtosis + 3 + ((3 * (n - 1) ** 2) / ((n - 2) * (n - 3)))
        bimodality_coefficient = numerator / denominator if denominator != 0 else 0.0
    else:
        bimodality_coefficient = 0.0

    heavy_tail_score = abs(kurtosis)

    # Use Bimodality Coefficient as the primary multimodality score
    multimodality_score = float(min(bimodality_coefficient, 1.0))

    variance = cast(float, clean.var())
    value_range = float(clean.max() - clean.min())
    low_variance_indicator = float(variance / value_range) if value_range != 0 else 0.0

    return BehavioralMetrics(
        outlier_ratio=outlier_ratio,
        heavy_tail_score=heavy_tail_score,
        multimodality_score=multimodality_score,
        low_variance_indicator=low_variance_indicator,
    )
