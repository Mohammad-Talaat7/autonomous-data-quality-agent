from queue import Queue
from typing import Any, override
from uuid import UUID

from ..events import TraceEvent
from .base import TraceStore


class QueueTraceStore(TraceStore):
    """
    Trace store that pushes events to a Python queue.
    Useful for real-time interop (e.g. with Rust TUI).
    """

    def __init__(self, queue: "Queue[Any]") -> None:
        self._queue = queue

    @override
    def append(self, event: TraceEvent) -> None:
        # Push event as dict for easier serialization/interop
        self._queue.put(event.to_dict())

    @override
    def get(self, trace_id: UUID) -> list[TraceEvent]:
        # Not implemented for queue store
        return []
