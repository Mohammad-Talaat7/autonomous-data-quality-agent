from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..models.column_profile import LogicalType
from ..models.metrics import BehavioralMetrics
from ..structural.summary import ColumnSummary
from .categorical_behavior import compute_categorical_behavior
from .numeric_behavior import compute_numeric_behavior


def compute_behavioral_metrics(
    summary: ColumnSummary,
    logical_type: LogicalType,
    thresholds: ProfilingThresholds | None = None,
) -> BehavioralMetrics | None:
    if logical_type == LogicalType.NUMERIC:
        return compute_numeric_behavior(summary, thresholds=thresholds)

    if logical_type == LogicalType.CATEGORICAL:
        return compute_categorical_behavior(summary, thresholds=thresholds)

    return None
