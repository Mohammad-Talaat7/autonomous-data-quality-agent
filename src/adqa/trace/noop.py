# adqa/trace/noop.py

from collections.abc import Iterable
from typing import override
from uuid import UUID

from .enums import TraceValue
from .events import TraceEvent
from .store.base import TraceStore


class NoOpTraceStore(TraceStore):
    @override
    def append(self, event: TraceEvent) -> None:
        pass

    @override
    def get(self, trace_id: UUID) -> Iterable[TraceEvent]:
        return []


class NoOpTraceEmitter:
    def __init__(self) -> None:
        from .context import TraceContext

        self.context = TraceContext()

    def emit(self, event: TraceEvent) -> None:
        pass


class NoOpLineageRecorder:
    def record(
        self,
        *,
        trace_id: UUID,
        operation: str,
        inputs: TraceValue | None,
        outputs: TraceValue | None,
        metadata: dict[str, TraceValue] | None = None,
    ) -> None:
        pass
