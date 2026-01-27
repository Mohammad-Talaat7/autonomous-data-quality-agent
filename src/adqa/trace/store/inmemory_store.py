# src/adqa/trace/store/memory.py

from collections import defaultdict
from typing_extensions import override
from uuid import UUID

from ..events import TraceEvent
from .base import TraceStore


class InMemoryTraceStore(TraceStore):
    """
    Append-only, in-memory trace store.
    Suitable for development and testing.
    """

    def __init__(self) -> None:
        self._events: defaultdict[UUID, list[TraceEvent]] = defaultdict(list)

    @override
    def append(self, event: TraceEvent) -> None:
        self._events[event.trace_id].append(event)

    @override
    def get(self, trace_id: UUID) -> list[TraceEvent]:
        return list(self._events.get(trace_id, []))
