from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from ..models.column_profile import LogicalType
from .summary import ColumnSummary

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds


def infer_logical_type(
    summary: ColumnSummary, thresholds: ProfilingThresholds | None = None
) -> LogicalType:
    """
    Infer logical type from pandas dtype and multi-factor content inspection.
    """
    dtype = summary.dtype

    # Use defaults if not provided
    text_len = thresholds.text_mean_length if thresholds else 50
    cat_count = thresholds.categorical_unique_count if thresholds else 100
    cat_ratio = thresholds.categorical_unique_ratio if thresholds else 0.1

    if pd.api.types.is_bool_dtype(dtype):
        return LogicalType.BOOLEAN

    if pd.api.types.is_numeric_dtype(dtype):
        return LogicalType.NUMERIC

    if pd.api.types.is_datetime64_any_dtype(dtype):
        return LogicalType.DATETIME

    if pd.api.types.is_string_dtype(dtype):
        if summary.clean_count == 0:
            return LogicalType.TEXT

        unique_ratio = summary.unique_count / summary.clean_count

        # Robust Categorical vs Text heuristic:
        is_short = (summary.mean_length or 0) < text_len
        is_low_cardinality = summary.unique_count < cat_count
        is_low_ratio = unique_ratio < cat_ratio

        if is_short and (is_low_cardinality or is_low_ratio):
            return LogicalType.CATEGORICAL

        return LogicalType.TEXT

    return LogicalType.UNKNOWN
