# src/adqa/trace/lineage/model.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
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
