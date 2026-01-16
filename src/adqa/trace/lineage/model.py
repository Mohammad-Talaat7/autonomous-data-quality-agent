# src/adqa/trace/lineage/model.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from adqa.trace.enums import TraceValue


@dataclass(frozen=True)
class LineageNode:
    """
    Represents a single data transformation or derivation.
    """

    operation: str
    inputs: list[str]
    outputs: list[str]

    node_id: UUID = field(default_factory=uuid4)
    trace_id: UUID = field(default_factory=uuid4)

    metadata: dict[str, TraceValue] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
