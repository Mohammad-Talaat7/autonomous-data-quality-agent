# adqa/config/model.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from ..data_ingress.datasource import DataSource
from .errors import ConfigError

type JsonValue = (
    dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None
)


class ExecutionMode(StrEnum):
    ADVISORY = "advisory"
    HUMAN_IN_LOOP = "human"
    AUTOMATIC = "automatic"


class TraceStoreType(StrEnum):
    IN_MEMORY = "in_memory"
    JSONL = "jsonl"


class ProfilingThresholds(BaseModel):
    # Logical Type Inference
    text_mean_length: int = 50
    categorical_unique_count: int = 100
    categorical_unique_ratio: float = 0.1

    # Behavioral
    min_rows_numeric_behavior: int = 5
    outlier_iqr_multiplier: float = 1.5
    rare_category_threshold: float = 0.01

    # ML & Semantic
    semantic_min_confidence: float = 0.4
    semantic_sample_size: int = 100
    semantic_weight_pattern: float = 0.7
    semantic_weight_keyword: float = 0.3
    min_rows_anomaly_detection: int = 20
    anomaly_contamination: str | float = "auto"
    anomaly_n_estimators: int = 50

    # Relational
    min_numeric_cols_for_correlation: int = 2

    # Performance & General
    summary_sample_size: int = 1000
    global_seed: int = 42


class ProfilingConfig(BaseModel):
    enable_ml: bool = False
    enable_correlation: bool = True
    correlation_method: Literal["pearson", "kendall", "spearman"] = "pearson"
    rounding_precision: int = 4

    # Parallelization & Sampling settings
    max_workers: int | None = None
    sampling_threshold: int = 50000
    sample_size: int = 10000

    # Thresholds
    thresholds: ProfilingThresholds = ProfilingThresholds()


class ADQAConfig(BaseModel):
    data_source: DataSource
    tracing_enabled: bool = False
    lineage_enabled: bool = False
    ml_enabled: bool = False
    trace_store: TraceStoreType | None = None
    execution_mode: ExecutionMode = ExecutionMode.ADVISORY
    profiling: ProfilingConfig = ProfilingConfig()

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, arbitrary_types_allowed=True
    )

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: dict[str, Any]) -> dict[str, Any]:
        tracing = data.get("tracing_enabled", False)
        if tracing and data.get("trace_store") is None:
            data["trace_store"] = TraceStoreType.IN_MEMORY
        if not tracing:
            data["trace_store"] = None
        return data

    @model_validator(mode="after")
    def validate_config(self) -> ADQAConfig:
        # Lineage requires tracing
        if self.lineage_enabled and not self.tracing_enabled:
            raise ConfigError("Lineage cannot be enabled without tracing")

        # Automatic execution requires tracing
        if self.execution_mode == ExecutionMode.AUTOMATIC and not self.tracing_enabled:
            raise ConfigError("Automatic execution requires tracing")

        # Human-in-loop requires tracing
        if (
            self.execution_mode == ExecutionMode.HUMAN_IN_LOOP
            and not self.tracing_enabled
        ):
            raise ConfigError("Human-in-loop execution requires tracing")

        return self


@dataclass
class ConfigSnapshot:
    config: ADQAConfig

    def to_json(self) -> dict[str, JsonValue]:
        return self.config.model_dump(mode="json")

    def hash(self) -> str:
        import hashlib
        import json

        s = json.dumps(self.to_json(), sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()


def snapshot_from_config(config: ADQAConfig) -> ConfigSnapshot:
    return ConfigSnapshot(config)
