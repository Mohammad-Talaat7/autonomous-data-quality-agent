from uuid import uuid4

import pytest

from adqa.trace.lineage.memory import InMemoryLineageAdapter
from adqa.trace.lineage.recorder import LineageRecorder


def test_recorder_initial_state() -> None:
    recorder = LineageRecorder()
    assert recorder.enabled is False


def test_recorder_enable_disable() -> None:
    adapter = InMemoryLineageAdapter()
    recorder = LineageRecorder(adapter=adapter)

    recorder.enable()
    assert recorder.enabled is True

    recorder.disable()
    assert recorder.enabled is False


def test_recorder_enable_without_adapter_raises() -> None:
    recorder = LineageRecorder(adapter=None)
    with pytest.raises(RuntimeError, match="Cannot enable lineage without an adapter"):
        recorder.enable()


def test_recorder_record_when_enabled() -> None:
    adapter = InMemoryLineageAdapter()
    recorder = LineageRecorder(adapter=adapter, enabled=True)
    trace_id = uuid4()

    recorder.record(
        trace_id=trace_id,
        operation="test_op",
        inputs=["in"],
        outputs=["out"],
        metadata={"m": 1},
    )

    nodes = adapter.get(trace_id)
    assert len(nodes) == 1
    assert nodes[0].operation == "test_op"
    assert nodes[0].metadata == {"m": 1}


def test_recorder_record_when_disabled() -> None:
    adapter = InMemoryLineageAdapter()
    recorder = LineageRecorder(adapter=adapter, enabled=False)
    trace_id = uuid4()

    recorder.record(
        trace_id=trace_id, operation="test_op", inputs=["in"], outputs=["out"]
    )

    assert len(adapter.get(trace_id)) == 0


def test_recorder_start_trace_when_enabled() -> None:
    adapter = InMemoryLineageAdapter()
    recorder = LineageRecorder(adapter=adapter, enabled=True)
    trace_id = uuid4()

    # Just verify it doesn't crash and calls through
    recorder.start_trace(trace_id)


def test_recorder_get_returns_empty_without_adapter() -> None:
    recorder = LineageRecorder(adapter=None)
    assert list(recorder.get(uuid4())) == []
