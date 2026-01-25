# adqa/config/model.py

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, model_validator

from ..data_ingress.config import DataSourceConfig
from .errors import ConfigError


class ExecutionMode(str, Enum):
    ADVISORY = "advisory"
    HUMAN_IN_LOOP = "human"
    AUTOMATIC = "automatic"


class TraceStoreType(str, Enum):
    IN_MEMORY = "in_memory"
    JSONL = "jsonl"


class ADQAConfig(BaseModel):
    tracing_enabled: bool
    lineage_enabled: bool
    ml_enabled: bool
    trace_store: TraceStoreType | None
    execution_mode: ExecutionMode
    data_source: DataSourceConfig

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_config(self) -> "ADQAConfig":
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

        # Trace store must be defined iff tracing is enabled
        if self.tracing_enabled and self.trace_store is None:
            raise ConfigError("trace_store must be set when tracing is enabled")

        if not self.tracing_enabled and self.trace_store is not None:
            raise ConfigError("trace_store must be None when tracing is disabled")

        return self
