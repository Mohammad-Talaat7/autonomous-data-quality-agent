from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..models.metrics import BehavioralMetrics
from ..structural.summary import ColumnSummary


def compute_categorical_behavior(
    summary: ColumnSummary, thresholds: ProfilingThresholds | None = None
) -> BehavioralMetrics | None:
    clean = summary.clean_series

    total = summary.clean_count
    if total == 0:
        return None

    rare_thresh = thresholds.rare_category_threshold if thresholds else 0.01

    # Use pre-calculated value_counts if available
    value_counts = (
        summary.value_counts
        if summary.value_counts is not None
        else clean.value_counts()
    )

    probabilities = value_counts / total

    dominance_ratio = float(probabilities.iloc[0])

    # Rare categories defined structurally (frequency < threshold)
    rare_ratio = float((probabilities < rare_thresh).sum() / len(probabilities))

    entropy = -np.sum(probabilities * np.log2(probabilities))
    max_entropy = np.log2(len(probabilities)) if len(probabilities) > 1 else 1
    imbalance_score = float(1 - (entropy / max_entropy))

    # For categorical, we reinterpret behavioral fields:
    return BehavioralMetrics(
        outlier_ratio=rare_ratio,
        heavy_tail_score=imbalance_score,
        multimodality_score=dominance_ratio,
        low_variance_indicator=imbalance_score,
    )
