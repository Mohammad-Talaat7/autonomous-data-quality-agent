from __future__ import annotations

import unittest
from uuid import UUID, uuid4

from adqa.trace.enums import TraceComponent, TraceEventType, TraceSeverity
from adqa.trace.reasoning import ReasonCode, ReasoningTraceEvent


class TestReasonCode(unittest.TestCase):
    def test_constants(self) -> None:
        """Test that ReasonCode constants are correct."""
        self.assertEqual(ReasonCode.HIGH_NULL_RATIO, "high_null_ratio")
        self.assertEqual(ReasonCode.LOW_CARDINALITY, "low_cardinality")
        self.assertEqual(ReasonCode.OUTLIER_DETECTED, "outlier_detected")
        self.assertEqual(ReasonCode.RULE_VIOLATION, "rule_violation")
        self.assertEqual(
            ReasonCode.METRIC_THRESHOLD_EXCEEDED, "metric_threshold_exceeded"
        )
        self.assertEqual(ReasonCode.CRITICAL_COLUMN, "critical_column")


class TestReasoningTraceEvent(unittest.TestCase):
    def test_creation_defaults(self) -> None:
        """Test creation with minimal arguments and default values."""
        # Note: 'reasons' is required by __post_init__ validation
        event = ReasoningTraceEvent(reasons=[ReasonCode.HIGH_NULL_RATIO])

        self.assertIsInstance(event.execution_event_id, UUID)
        self.assertEqual(event.confidence, 0.0)
        self.assertEqual(event.reasons, [ReasonCode.HIGH_NULL_RATIO])
        self.assertEqual(event.evidence, {})

        # Verify enforced fields from __post_init__
        self.assertEqual(event.component, TraceComponent.TRACE)
        self.assertEqual(event.event_type, TraceEventType.DECISION)
        self.assertEqual(event.severity, TraceSeverity.INFO)

    def test_creation_full(self) -> None:
        """Test creation with all arguments provided."""
        exec_id = uuid4()
        event = ReasoningTraceEvent(
            execution_event_id=exec_id,
            confidence=0.85,
            reasons=[ReasonCode.HIGH_NULL_RATIO, ReasonCode.CRITICAL_COLUMN],
            evidence={"null_ratio": 0.5},
            name="decision_event",  # Base class field
        )

        self.assertEqual(event.execution_event_id, exec_id)
        self.assertEqual(event.confidence, 0.85)
        self.assertEqual(
            event.reasons, [ReasonCode.HIGH_NULL_RATIO, ReasonCode.CRITICAL_COLUMN]
        )
        self.assertEqual(event.evidence, {"null_ratio": 0.5})
        self.assertEqual(event.name, "decision_event")

    def test_confidence_validation(self) -> None:
        """Test that confidence must be between 0.0 and 1.0."""
        with self.assertRaises(ValueError):
            _ = ReasoningTraceEvent(reasons=["r"], confidence=-0.1)

        with self.assertRaises(ValueError):
            _ = ReasoningTraceEvent(reasons=["r"], confidence=1.1)

    def test_reasons_validation(self) -> None:
        """Test that reasons list cannot be empty."""
        with self.assertRaises(ValueError):
            _ = ReasoningTraceEvent(reasons=[])

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        exec_id = uuid4()
        event = ReasoningTraceEvent(
            execution_event_id=exec_id,
            confidence=0.9,
            reasons=[ReasonCode.OUTLIER_DETECTED],
            evidence={"score": 10.0},
        )

        data = event.to_dict()

        # Check base fields
        self.assertEqual(data["component"], "trace")
        self.assertEqual(data["event_type"], "decision")

        # Check subclass fields
        self.assertEqual(data["execution_event_id"], str(exec_id))
        self.assertEqual(data["confidence"], 0.9)
        self.assertEqual(data["reasons"], ["outlier_detected"])
        self.assertEqual(data["evidence"], {"score": 10.0})


if __name__ == "__main__":
    _ = unittest.main()
