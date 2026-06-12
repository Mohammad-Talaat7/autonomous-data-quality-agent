# tests/trace/test_emitter.py

from unittest.mock import Mock
from uuid import uuid4

import pytest
from adqa.trace.context import TraceContext
from adqa.trace.emitter import TraceEmitter
from adqa.trace.events import TraceEvent
from adqa.trace.store.base import TraceStore


class TestTraceEmitter:
    def test_init_requires_store_if_enabled(self) -> None:
        context = TraceContext()
        with pytest.raises(ValueError, match="store_traces=True requires a TraceStore"):
            _ = TraceEmitter(context, store_traces=True)

    def test_emit_ignores_if_disabled(self) -> None:
        context = TraceContext()
        store = Mock(spec=TraceStore)
        emitter = TraceEmitter(context, store=store, store_traces=False)

        event = TraceEvent(trace_id=context.trace_id)
        emitter.emit(event)
        store.append.assert_not_called()  # pyright: ignore[reportAny]

    def test_emit_appends_to_store_if_enabled(self) -> None:
        context = TraceContext()
        store = Mock(spec=TraceStore)
        emitter = TraceEmitter(context, store=store, store_traces=True)

        event = TraceEvent(trace_id=context.trace_id)
        emitter.emit(event)
        store.append.assert_called_once_with(event)  # pyright: ignore[reportAny]

    def test_emit_validates_trace_id_match(self) -> None:
        context = TraceContext()
        store = Mock(spec=TraceStore)
        emitter = TraceEmitter(context, store=store, store_traces=True)

        # Event with different trace_id
        event = TraceEvent(trace_id=uuid4())

        with pytest.raises(ValueError, match="TraceEvent.trace_id does not match"):
            emitter.emit(event)

        store.append.assert_not_called()  # pyright: ignore[reportAny]

    def test_emit_ignores_id_mismatch_if_disabled(self) -> None:
        """
        If tracing is disabled, we should return early BEFORE validating the trace_id.
        This prevents raising errors for harmless events in production.
        """
        context = TraceContext()
        store = Mock(spec=TraceStore)
        # store_traces defaults to False
        emitter = TraceEmitter(context, store=store, store_traces=False)

        # Event with mismatched trace_id
        event = TraceEvent(trace_id=uuid4())

        # Should NOT raise ValueError
        emitter.emit(event)

        store.append.assert_not_called()  # pyright: ignore[reportAny]
