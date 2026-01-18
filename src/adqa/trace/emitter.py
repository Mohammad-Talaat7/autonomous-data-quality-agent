# src/adqa/trace/emitter.py
from .context import TraceContext
from .events import TraceEvent
from .store.base import TraceStore


class TraceEmitter:
    """
    Controls whether trace events are emitted to a TraceStore.
    """

    def __init__(
        self,
        context: TraceContext,
        *,
        store: TraceStore | None = None,
        store_traces: bool = False,
    ) -> None:
        self.context: TraceContext = context
        self._store: TraceStore | None = store
        self._store_traces: bool = store_traces

        if self._store_traces and self._store is None:
            raise ValueError("store_traces=True requires a TraceStore to be provided")

    def emit(self, event: TraceEvent) -> None:
        if not self._store_traces or self._store is None:
            return

        if event.trace_id != self.context.trace_id:
            raise ValueError("TraceEvent.trace_id does not match TraceContext.trace_id")

        self._store.append(event)
