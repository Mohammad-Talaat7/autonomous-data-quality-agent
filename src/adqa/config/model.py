# adqa/config/model.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, model_validator

from ..data_ingress.datasource import DataSource
from .errors import ConfigError

type JsonValue = (
    dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None
)


class ExecutionMode(str, Enum):
    ADVISORY = "advisory"
    HUMAN_IN_LOOP = "human"
    AUTOMATIC = "automatic"


class TraceStoreType(str, Enum):
    IN_MEMORY = "in_memory"
    JSONL = "jsonl"


class ADQAConfig(BaseModel):
    data_source: DataSource
    tracing_enabled: bool = False
    lineage_enabled: bool = False
    ml_enabled: bool = False
    trace_store: TraceStoreType | None = None
    execution_mode: ExecutionMode = ExecutionMode.ADVISORY

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
