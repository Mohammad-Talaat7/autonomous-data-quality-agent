from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .column_profile import ColumnProfile
from .correlation_profile import CorrelationProfile


@dataclass(frozen=True)
class DatasetMetadata:
    row_count: int
    column_count: int
    duplicate_row_ratio: float
    memory_usage_bytes: int
    total_null_ratio: float
    type_distribution: Mapping[str, int]


@dataclass(frozen=True)
class DatasetProfile:
    metadata: DatasetMetadata
    columns: tuple[ColumnProfile, ...]
    correlations: CorrelationProfile | None
