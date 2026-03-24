# tests/trace/test_noop.py

from uuid import uuid4

from adqa.trace.events import TraceEvent
from adqa.trace.noop import NoOpLineageRecorder, NoOpTraceEmitter, NoOpTraceStore


class TestNoOpTraceStore:
    def test_append_does_nothing(self):
        store = NoOpTraceStore()
        event = TraceEvent()
        # Should not raise
        store.append(event)

    def test_get_returns_empty_list(self):
        store = NoOpTraceStore()
        trace_id = uuid4()
        result = store.get(trace_id)
        assert result == []


class TestNoOpTraceEmitter:
    def test_emit_does_nothing(self):
        emitter = NoOpTraceEmitter()
        event = TraceEvent()
        # Should not raise
        emitter.emit(event)


class TestNoOpLineageRecorder:
    def test_record_does_nothing(self):
        recorder = NoOpLineageRecorder()
        trace_id = uuid4()
        # Should not raise
        recorder.record(
            trace_id=trace_id,
            operation="test_op",
            inputs={"a": 1},
            outputs={"b": 2},
        )
