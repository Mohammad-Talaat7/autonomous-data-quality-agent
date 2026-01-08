# Define a storage contract

from abc import ABC, abstractmethod
from collections.abc import Iterable
from uuid import UUID

from adqa.trace.events import TraceEvent


class TraceStore(ABC):
    """
    Abstract interface for trace event storage.
    """

    @abstractmethod
    def append(self, event: TraceEvent) -> None:
        """Append a TraceEvent to the store (append-only)."""

    @abstractmethod
    def get(self, trace_id: UUID) -> Iterable[TraceEvent]:
        """Retrieve all events for a trace_id in deterministic order."""
