from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

import pandas as pd


@dataclass(frozen=True)
class ColumnSummary:
    """
    Pre-calculated statistics for a single pass profiling.
    """

    name: str
    dtype: Any
    total_count: int
    null_count: int
    memory_usage: int
    clean_series: pd.Series[Any]
    unique_count: int
    value_counts: pd.Series[Any] | None = None
    mean_length: float | None = None

    @property
    def null_ratio(self) -> float:
        return self.null_count / self.total_count if self.total_count > 0 else 0.0

    @property
    def clean_count(self) -> int:
        return len(self.clean_series)


def build_column_summary(
    series: pd.Series[Any],
    compute_counts: bool = True,
    thresholds: ProfilingThresholds | None = None,
) -> ColumnSummary:
    """
    Compute column summary statistics in a single pass.
    """
    total = len(series)
    null_count = int(series.isna().sum())
    memory = int(series.memory_usage(deep=True))
    clean = series.dropna()

    unique_count = 0
    value_counts = None
    mean_length = None

    sample_size = thresholds.summary_sample_size if thresholds else 1000

    if pd.api.types.is_string_dtype(series.dtype) and not clean.empty:
        # Sample for mean length to stay fast
        sample = clean.head(sample_size).astype(str)
        mean_length = float(sample.str.len().mean())

    if compute_counts and not clean.empty:
        # If it's likely categorical or we just want counts, compute value_counts
        # This gives us unique_count for free.
        value_counts = clean.value_counts()
        unique_count = len(value_counts)
    elif not clean.empty:
        # Just unique count if value_counts not requested
        unique_count = int(clean.nunique())

    return ColumnSummary(
        name=str(series.name),
        dtype=series.dtype,
        total_count=total,
        null_count=null_count,
        memory_usage=memory,
        clean_series=clean,
        unique_count=unique_count,
        value_counts=value_counts,
        mean_length=mean_length,
    )
