from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

import pandas as pd

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..models.column_profile import ColumnProfile, LogicalType
from ..models.correlation_profile import CorrelationProfile


def _get_numeric_columns(columns: tuple[ColumnProfile, ...]) -> tuple[str, ...]:
    """
    Extract numeric column names in deterministic sorted order.
    """
    numeric_cols = [
        col.name for col in columns if col.logical_type == LogicalType.NUMERIC
    ]
    return tuple(sorted(numeric_cols))


def _compute_correlation_matrix(
    df: pd.DataFrame,
    numeric_columns: tuple[str, ...],
    method: Literal["pearson", "kendall", "spearman"],
) -> dict[tuple[str, str], float]:
    """
    Compute full pairwise correlation matrix with deterministic ordering.
    """
    if not numeric_columns:
        return {}

    corr_df = df[list(numeric_columns)].corr(method=method)

    matrix: dict[tuple[str, str], float] = {}

    for col1 in numeric_columns:
        for col2 in numeric_columns:
            if col1 <= col2:  # avoid duplicate symmetric pairs
                value = corr_df.loc[col1, col2]
                if pd.notna(value):
                    matrix[(col1, col2)] = cast(float, value)

    return matrix


def _compute_max_abs_correlation_per_column(
    matrix: dict[tuple[str, str], float],
) -> dict[str, float]:
    """
    Compute maximum absolute correlation per column excluding self-correlation.
    """
    max_corr: dict[str, float] = {}

    for (col1, col2), value in matrix.items():
        if col1 == col2:
            continue

        abs_val = abs(value)

        max_corr[col1] = max(abs_val, max_corr.get(col1, 0.0))
        max_corr[col2] = max(abs_val, max_corr.get(col2, 0.0))

    return max_corr


def _compute_correlation_density_score(matrix: dict[tuple[str, str], float]) -> float:
    """
    Density score = average absolute correlation excluding self-correlations.
    """
    values = [abs(value) for (col1, col2), value in matrix.items() if col1 != col2]

    if not values:
        return 0.0

    return float(sum(values) / len(values))


def profile_correlations(
    df: pd.DataFrame,
    columns: tuple[ColumnProfile, ...],
    method: Literal["pearson", "kendall", "spearman"] = "pearson",
    thresholds: ProfilingThresholds | None = None,
) -> CorrelationProfile | None:
    """
    Full correlation profiling.
    """
    numeric_columns = _get_numeric_columns(columns)

    min_cols = thresholds.min_numeric_cols_for_correlation if thresholds else 2

    if len(numeric_columns) < min_cols:
        return None

    matrix = _compute_correlation_matrix(df, numeric_columns, method)
    max_corr = _compute_max_abs_correlation_per_column(matrix)
    density_score = _compute_correlation_density_score(matrix)

    return CorrelationProfile(
        method=method,
        matrix=matrix,
        max_abs_correlation_per_column=max_corr,
        correlation_density_score=density_score,
    )
