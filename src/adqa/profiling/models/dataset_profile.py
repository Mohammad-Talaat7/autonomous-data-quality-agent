from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "duplicate_row_ratio": self.duplicate_row_ratio,
            "memory_usage_bytes": self.memory_usage_bytes,
            "total_null_ratio": self.total_null_ratio,
            "type_distribution": dict(self.type_distribution),
        }


@dataclass(frozen=True)
class DatasetProfile:
    metadata: DatasetMetadata
    columns: tuple[ColumnProfile, ...]
    correlations: CorrelationProfile | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "columns": [c.to_dict() for c in self.columns],
            "correlations": self.correlations.to_dict() if self.correlations else None,
        }
