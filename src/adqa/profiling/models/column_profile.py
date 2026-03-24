from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

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
