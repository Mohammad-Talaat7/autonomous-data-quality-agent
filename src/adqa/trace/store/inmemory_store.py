# src/adqa/trace/store/memory.py

from collections import defaultdict
from typing import override
from uuid import UUID

from adqa.trace.events import TraceEvent
from adqa.trace.store.base import TraceStore


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
