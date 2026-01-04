from __future__ import annotations

import unittest
from datetime import datetime
from uuid import UUID, uuid4

from adqa.trace.enums import TraceComponent, TraceEventType, TraceSeverity
from adqa.trace.events import TraceEvent


class TestTraceEvent(unittest.TestCase):
    def test_default_creation(self) -> None:
        """Test that a TraceEvent can be created with default values."""
        event = TraceEvent()
        self.assertIsInstance(event.event_id, UUID)
        self.assertIsInstance(event.trace_id, UUID)
        self.assertEqual(event.component, TraceComponent.TRACE)
        self.assertEqual(event.event_type, TraceEventType.RESULT)
        self.assertEqual(event.severity, TraceSeverity.INFO)
        self.assertEqual(event.name, "")
        self.assertIsInstance(event.timestamp, datetime)
        self.assertIsNone(event.inputs)
        self.assertIsNone(event.outputs)
        self.assertEqual(event.metadata, {})
        self.assertIsNone(event.parent_event_id)

    def test_creation_with_values(self) -> None:
        """Test that a TraceEvent can be created with specified values."""
        event_id = uuid4()
        trace_id = uuid4()
        parent_event_id = uuid4()
        timestamp = datetime.now()
        event = TraceEvent(
            event_id=event_id,
            trace_id=trace_id,
            component=TraceComponent.METRIC,
            event_type=TraceEventType.START,
            severity=TraceSeverity.WARNING,
            name="my-event",
            timestamp=timestamp,
            inputs={"input_key": "input_value"},
            outputs={"output_key": "output_value"},
            metadata={"meta_key": "meta_value"},
            parent_event_id=parent_event_id,
        )
        self.assertEqual(event.event_id, event_id)
        self.assertEqual(event.trace_id, trace_id)
        self.assertEqual(event.component, TraceComponent.METRIC)
        self.assertEqual(event.event_type, TraceEventType.START)
        self.assertEqual(event.severity, TraceSeverity.WARNING)
        self.assertEqual(event.name, "my-event")
        self.assertEqual(event.timestamp, timestamp)
        self.assertEqual(event.inputs, {"input_key": "input_value"})
        self.assertEqual(event.outputs, {"output_key": "output_value"})
        self.assertEqual(event.metadata, {"meta_key": "meta_value"})
        self.assertEqual(event.parent_event_id, parent_event_id)

    def test_to_dict(self) -> None:
        """Test that the to_dict method returns the correct dictionary."""
        event_id = uuid4()
        trace_id = uuid4()
        parent_event_id = uuid4()
        timestamp = datetime.now()
        event = TraceEvent(
            event_id=event_id,
            trace_id=trace_id,
            component=TraceComponent.METRIC,
            event_type=TraceEventType.START,
            severity=TraceSeverity.WARNING,
            name="my-event",
            timestamp=timestamp,
            inputs={"input_key": "input_value"},
            outputs={"output_key": "output_value"},
            metadata={"meta_key": "meta_value"},
            parent_event_id=parent_event_id,
        )
        event_dict = event.to_dict()
        self.assertEqual(event_dict["event_id"], str(event_id))
        self.assertEqual(event_dict["trace_id"], str(trace_id))
        self.assertEqual(event_dict["parent_event_id"], str(parent_event_id))
        self.assertEqual(event_dict["component"], "metric")
        self.assertEqual(event_dict["event_type"], "start")
        self.assertEqual(event_dict["severity"], "warning")
        self.assertEqual(event_dict["name"], "my-event")
        self.assertEqual(event_dict["timestamp"], timestamp.isoformat())
        self.assertEqual(event_dict["inputs"], {"input_key": "input_value"})
        self.assertEqual(event_dict["outputs"], {"output_key": "output_value"})
        self.assertEqual(event_dict["metadata"], {"meta_key": "meta_value"})

    def test_to_dict_with_none(self) -> None:
        """Test that the to_dict method handles None values correctly."""
        event = TraceEvent()
        event_dict = event.to_dict()
        self.assertIsInstance(event_dict["event_id"], str)
        self.assertIsInstance(event_dict["trace_id"], str)
        self.assertIsNone(event_dict["parent_event_id"])
        self.assertEqual(event_dict["component"], "trace")
        self.assertEqual(event_dict["event_type"], "result")
        self.assertEqual(event_dict["severity"], "info")
        self.assertEqual(event_dict["name"], "")
        self.assertIsInstance(event_dict["timestamp"], str)
        self.assertIsNone(event_dict["inputs"])
        self.assertIsNone(event_dict["outputs"])
        self.assertEqual(event_dict["metadata"], {})


if __name__ == "__main__":
    _ = unittest.main()
