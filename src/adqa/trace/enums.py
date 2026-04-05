# adqa/trace/enums.py
# shared vocabulary for all tracing system.

from enum import StrEnum
from typing import TypedDict


class TraceComponent(StrEnum):
    METRIC = "metric"
    RULE = "rule"
    FIX = "fix"
    TRACE = "trace"
    LINEAGE = "lineage"
    AUDIT = "audit"


class TraceEventType(StrEnum):
    START = "start"
    END = "end"
    RESULT = "result"
    ERROR = "error"
    DECISION = "decision"
    EXECUTION = "execution"
    CHECK = "check"
    PROPOSAL = "proposal"
    SNAPSHOT = "snapshot"
    DATA_INGRESS = "data_ingress"
    PROFILING = "profiling"
    INFO = "info"


class TraceSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


TracePrimitive = str | int | float | bool | None

TraceValue = TracePrimitive | list["TraceValue"] | dict[str, "TraceValue"]


class TraceEventDict(TypedDict):
    event_id: str
    trace_id: str
    parent_event_id: str | None
    component: str
    event_type: str
    severity: str
    name: str
    timestamp: str
    inputs: dict[str, TraceValue] | None
    outputs: dict[str, TraceValue] | None
    metadata: dict[str, TraceValue]


class ReasoningTraceEventDict(TraceEventDict):
    execution_event_id: str
    confidence: float
    reasons: list[str]
    evidence: dict[str, TraceValue]
