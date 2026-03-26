# src/adqa/trace/emitter.py

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

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

    @contextmanager
    def span(self, name: str, **kwargs: Any) -> Iterator[Any]:
        """
        Syntactic sugar for execution_hook.
        """
        from .enums import TraceComponent, TraceEventType
        from .hooks.execution import execution_hook

        # Default to RULE/CHECK if not specified
        component = kwargs.pop("component", TraceComponent.RULE)
        event_type = kwargs.pop("event_type", TraceEventType.CHECK)

        with execution_hook(
            name=name,
            component=component,
            event_type=event_type,
            emitter=self,
            inputs=kwargs,
        ) as ctx:
            yield ctx
