from __future__ import annotations

import pandas as pd

from ..models.dataset_profile import DatasetMetadata


def compute_duplicate_row_ratio(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    duplicate_count = df.duplicated().sum()
    return float(duplicate_count / len(df))


def compute_total_null_ratio(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    total_cells = df.shape[0] * df.shape[1]
    if total_cells == 0:
        return 0.0
    return float(df.isna().sum().sum() / total_cells)


def compute_type_distribution(df: pd.DataFrame) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for dtype in df.dtypes:
        key = str(dtype)
        distribution[key] = distribution.get(key, 0) + 1
    return distribution


def profile_dataset_structure(df: pd.DataFrame) -> DatasetMetadata:
    row_count = len(df)
    column_count = len(df.columns)
    memory_usage = int(df.memory_usage(deep=True).sum())

    return DatasetMetadata(
        row_count=row_count,
        column_count=column_count,
        duplicate_row_ratio=compute_duplicate_row_ratio(df),
        memory_usage_bytes=memory_usage,
        total_null_ratio=compute_total_null_ratio(df),
        type_distribution=compute_type_distribution(df),
    )
