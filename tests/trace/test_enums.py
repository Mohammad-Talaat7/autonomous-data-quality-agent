# tests/trace/test_enums.py

from __future__ import annotations

import unittest

from adqa.trace.enums import TraceComponent, TraceEventType, TraceSeverity


class TestEnums(unittest.TestCase):
    def test_trace_component(self) -> None:
        """Test the values of the TraceComponent enum."""
        self.assertEqual(TraceComponent.METRIC, "metric")
        self.assertEqual(TraceComponent.RULE, "rule")
        self.assertEqual(TraceComponent.FIX, "fix")
        self.assertEqual(TraceComponent.TRACE, "trace")
        self.assertEqual(TraceComponent.LINEAGE, "lineage")
        self.assertEqual(TraceComponent.AUDIT, "audit")

    def test_trace_event_type(self) -> None:
        """Test the values of the TraceEventType enum."""
        self.assertEqual(TraceEventType.START, "start")
        self.assertEqual(TraceEventType.END, "end")
        self.assertEqual(TraceEventType.RESULT, "result")
        self.assertEqual(TraceEventType.ERROR, "error")
        self.assertEqual(TraceEventType.DECISION, "decision")

    def test_trace_severity(self) -> None:
        """Test the values of the TraceSeverity enum."""
        self.assertEqual(TraceSeverity.INFO, "info")
        self.assertEqual(TraceSeverity.WARNING, "warning")
        self.assertEqual(TraceSeverity.ERROR, "error")
        self.assertEqual(TraceSeverity.CRITICAL, "critical")


if __name__ == "__main__":
    _ = unittest.main()
