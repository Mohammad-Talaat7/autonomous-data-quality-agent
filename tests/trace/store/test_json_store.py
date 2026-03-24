import json
from pathlib import Path
from uuid import uuid4

import pytest
from adqa.trace.enums import TraceComponent, TraceEventType, TraceSeverity
from adqa.trace.events import TraceEvent
from adqa.trace.store.json_store import JSONTraceStore


class TestJSONTraceStore:
    def test_init_creates_file(self, tmp_path: Path) -> None:
        f = tmp_path / "trace.jsonl"
        assert not f.exists()

        _ = JSONTraceStore(f)
        assert f.exists()

    def test_append_writes_json_line(self, tmp_path: Path) -> None:
        f = tmp_path / "trace.jsonl"
        store = JSONTraceStore(f)
        trace_id = uuid4()

        event = TraceEvent(
            trace_id=trace_id,
            name="test_event",
            inputs={"a": 1},
            metadata={"meta": "data"},
        )

        store.append(event)

        lines = f.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])  # pyright: ignore[reportAny]
        assert data["trace_id"] == str(trace_id)
        assert data["name"] == "test_event"
        assert data["inputs"] == {"a": 1}

    def test_get_reconstructs_events(self, tmp_path: Path) -> None:
        f = tmp_path / "trace.jsonl"
        store = JSONTraceStore(f)
        trace_id = uuid4()

        # Create a fully populated event to test all fields
        parent_id = uuid4()
        event = TraceEvent(
            trace_id=trace_id,
            parent_event_id=parent_id,
            component=TraceComponent.RULE,
            event_type=TraceEventType.DECISION,
            severity=TraceSeverity.WARNING,
            name="complex_event",
            inputs={"x": 10},
            outputs={"y": 20},
            metadata={"tag": "v1"},
        )

        store.append(event)

        # Read back
        # Create new store instance to ensure we read from disk
        store_read = JSONTraceStore(f)
        events = store_read.get(trace_id)

        assert len(events) == 1
        read_event = events[0]

        assert read_event.event_id == event.event_id
        assert read_event.trace_id == event.trace_id
        assert read_event.parent_event_id == event.parent_event_id
        assert read_event.component == event.component
        assert read_event.event_type == event.event_type
        assert read_event.severity == event.severity
        assert read_event.name == event.name
        # Timestamps might lose microsecond precision depending on ISO format
        # But datetime.fromisoformat usually handles what isoformat() produces.
        assert read_event.timestamp == event.timestamp
        assert read_event.inputs == event.inputs
        assert read_event.outputs == event.outputs
        assert read_event.metadata == event.metadata

    def test_get_filters_trace_id(self, tmp_path: Path) -> None:
        f = tmp_path / "trace.jsonl"
        store = JSONTraceStore(f)

        t1 = uuid4()
        t2 = uuid4()

        e1 = TraceEvent(trace_id=t1, name="e1")
        e2 = TraceEvent(trace_id=t2, name="e2")
        e3 = TraceEvent(trace_id=t1, name="e3")

        store.append(e1)
        store.append(e2)
        store.append(e3)

        events_t1 = store.get(t1)
        assert len(events_t1) == 2
        assert events_t1[0].name == "e1"
        assert events_t1[1].name == "e3"

        events_t2 = store.get(t2)
        assert len(events_t2) == 1
        assert events_t2[0].name == "e2"

    def test_round_trip_sparse_event(self, tmp_path: Path) -> None:
        """Test event with None values for optional fields."""
        f = tmp_path / "trace.jsonl"
        store = JSONTraceStore(f)
        trace_id = uuid4()

        event = TraceEvent(
            trace_id=trace_id,
            name="sparse",
            parent_event_id=None,
            inputs=None,
            outputs=None,
        )

        store.append(event)

        events = store.get(trace_id)
        assert len(events) == 1
        assert events[0].parent_event_id is None
        assert events[0].inputs is None
        assert events[0].outputs is None

    def test_round_trip_special_characters(self, tmp_path: Path) -> None:
        """Test newlines and unicode in string fields."""
        f = tmp_path / "trace.jsonl"
        store = JSONTraceStore(f)
        trace_id = uuid4()

        # Newlines should be escaped in JSON, preserving line-based format
        name_with_newline = "line1\nline2"
        meta_with_unicode = {"emoji": "🧪"}

        event = TraceEvent(
            trace_id=trace_id,
            name=name_with_newline,
            metadata=meta_with_unicode,  # pyright: ignore[reportArgumentType]
        )

        store.append(event)

        # Verify file structure (still one line)
        content = f.read_text(encoding="utf-8")
        assert len(content.splitlines()) == 1

        # Verify data integrity
        events = store.get(trace_id)
        assert len(events) == 1
        assert events[0].name == name_with_newline
        assert events[0].metadata == meta_with_unicode

    def test_get_handles_corrupted_lines(self, tmp_path: Path) -> None:
        """Test that get raises JSONDecodeError (or handles it) on bad data."""
        f = tmp_path / "trace.jsonl"
        _ = f.write_text('{"valid": "json"}\n{invalid_json', encoding="utf-8")

        store = JSONTraceStore(f)

        # Currently the implementation does not try/except json.loads,
        # so we expect it to raise. This confirms behavior.
        with pytest.raises(json.JSONDecodeError):
            _ = store.get(uuid4())
