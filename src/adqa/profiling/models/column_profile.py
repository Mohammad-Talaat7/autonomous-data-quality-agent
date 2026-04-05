from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .metrics import (
    BehavioralMetrics,
    CategoricalMetrics,
    DatetimeMetrics,
    NumericMetrics,
    StructuralMetrics,
    TextMetrics,
)


class LogicalType(StrEnum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class SemanticTag(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    IDENTIFIER = "identifier"
    TARGET = "target"
    TIMESTAMP = "timestamp"
    COUNTRY_CODE = "country_code"
    FREE_TEXT = "free_text"


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    dtype: str
    logical_type: LogicalType

    structural_metrics: StructuralMetrics

    numeric_metrics: NumericMetrics | None = None
    categorical_metrics: CategoricalMetrics | None = None
    datetime_metrics: DatetimeMetrics | None = None
    text_metrics: TextMetrics | None = None

    behavioral_metrics: BehavioralMetrics | None = None

    semantic_tags: tuple[SemanticTag, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "logical_type": self.logical_type.value,
            "structural_metrics": self.structural_metrics.to_dict(),
            "numeric_metrics": (
                self.numeric_metrics.to_dict() if self.numeric_metrics else None
            ),
            "categorical_metrics": (
                self.categorical_metrics.to_dict() if self.categorical_metrics else None
            ),
            "datetime_metrics": (
                self.datetime_metrics.to_dict() if self.datetime_metrics else None
            ),
            "text_metrics": self.text_metrics.to_dict() if self.text_metrics else None,
            "behavioral_metrics": (
                self.behavioral_metrics.to_dict() if self.behavioral_metrics else None
            ),
            "semantic_tags": [t.value for t in self.semantic_tags],
        }
