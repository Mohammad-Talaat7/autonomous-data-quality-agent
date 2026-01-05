# the atomic unit of observability.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from adqa.trace.enums import (
    TraceComponent,
    TraceEventDict,
    TraceEventType,
    TraceSeverity,
    TraceValue,
)


@dataclass
class TraceEvent:
    """
    Base trace event.
    All specialized events extend or compose this.
    """

    event_id: UUID = field(default_factory=uuid4)
    trace_id: UUID = field(default_factory=uuid4)

    component: TraceComponent = TraceComponent.TRACE
    event_type: TraceEventType = TraceEventType.RESULT
    severity: TraceSeverity = TraceSeverity.INFO

    name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    inputs: dict[str, TraceValue] | None = None
    outputs: dict[str, TraceValue] | None = None
    metadata: dict[str, TraceValue] = field(default_factory=dict)

    parent_event_id: UUID | None = None

    def to_dict(self) -> TraceEventDict:
        return {
            "event_id": str(self.event_id),
            "trace_id": str(self.trace_id),
            "parent_event_id": (
                str(self.parent_event_id) if self.parent_event_id else None
            ),
            "component": self.component.value,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metadata": self.metadata,
        }
