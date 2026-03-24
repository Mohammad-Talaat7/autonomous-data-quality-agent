# adqa/trace/context.py
# identify and scope a trace session.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TraceContext:
    """
    Identifies a single ADQA execution context.
    """

    trace_id: UUID = field(default_factory=uuid4)
    dataset_id: str | None = None
    parent_trace_id: UUID | None = None
    mode: str = "advisory"  # advisory | execution
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def to_dict(self) -> dict[str, str | None]:
        return {
            "trace_id": str(self.trace_id),
            "dataset_id": self.dataset_id,
            "parent_trace_id": (
                str(self.parent_trace_id) if self.parent_trace_id else None
            ),
            "mode": self.mode,
            "created_at": self.created_at.isoformat(),
        }
