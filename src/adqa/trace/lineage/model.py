# adqa/trace/lineage/model.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from ..enums import TraceValue


@dataclass(frozen=True)
class LineageNode:
    """
    Represents a single data transformation or derivation.
    """

    operation: str
    inputs: TraceValue | None
    outputs: TraceValue | None

    node_id: UUID = field(default_factory=uuid4)
    trace_id: UUID = field(default_factory=uuid4)

    metadata: dict[str, TraceValue] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def to_dict(self) -> dict[str, Any]:
        from ..hooks.serialize import to_trace_value

        return {
            "node_id": str(self.node_id),
            "trace_id": str(self.trace_id),
            "operation": self.operation,
            "inputs": to_trace_value(self.inputs),
            "outputs": to_trace_value(self.outputs),
            "metadata": {k: to_trace_value(v) for k, v in self.metadata.items()},
            "timestamp": self.timestamp.isoformat(),
        }
