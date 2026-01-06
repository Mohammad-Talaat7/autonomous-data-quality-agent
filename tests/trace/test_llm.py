from __future__ import annotations

import unittest
from uuid import uuid4

from adqa.trace.context import TraceContext
from adqa.trace.emitter import TraceEmitter
from adqa.trace.enums import TraceComponent, TraceEventType
from adqa.trace.llm import DecisionRecord, LLMReasoningLayer
from adqa.trace.store.inmemory_store import InMemoryTraceStore


class TestLLMReasoningLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.context = TraceContext()
        self.store = InMemoryTraceStore()
        self.emitter = TraceEmitter(self.context, store=self.store, store_traces=True)
        self.reasoning_layer = LLMReasoningLayer(self.context, self.emitter)

    def test_record_decision(self) -> None:
        """Test recording a decision event."""
        decision = DecisionRecord(
            decision_type="APPLY_FIX",
            rationale="Data pattern matches known anomaly.",
            confidence_score=0.95,
            alternatives_considered=["DELETE_ROW"],
            model_name="test-model",
        )
        inputs = {"raw_data": "some value"}

        event = self.reasoning_layer.record_decision(
            name="test_decision",
            decision=decision,
            inputs=inputs,
        )

        self.assertEqual(event.trace_id, self.context.trace_id)
        self.assertEqual(event.component, TraceComponent.DECISION)
        self.assertEqual(event.event_type, TraceEventType.DECISION)
        self.assertEqual(event.name, "test_decision")
        self.assertEqual(event.inputs, inputs)
        self.assertEqual(event.outputs, decision.to_dict())

        # Verify it was stored
        events = self.store.get(self.context.trace_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], event)

    def test_record_execution_linked_to_decision(self) -> None:
        """Test recording an execution event linked to a decision."""
        decision_event_id = uuid4()
        inputs = {"action": "fix"}
        outputs = {"status": "success"}

        event = self.reasoning_layer.record_execution(
            name="apply_fix",
            decision_event_id=decision_event_id,
            inputs=inputs,
            outputs=outputs,
        )

        self.assertEqual(event.trace_id, self.context.trace_id)
        self.assertEqual(event.parent_event_id, decision_event_id)
        self.assertEqual(event.component, TraceComponent.FIX)
        self.assertEqual(event.event_type, TraceEventType.RESULT)
        self.assertEqual(event.name, "apply_fix")
        self.assertEqual(event.inputs, inputs)
        self.assertEqual(event.outputs, outputs)

        # Verify it was stored
        events = self.store.get(self.context.trace_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], event)

    def test_full_chain(self) -> None:
        """Test the full chain of decision and execution."""
        # 1. Record Decision
        decision = DecisionRecord(
            decision_type="CLEAN",
            rationale="Reasoning...",
            confidence_score=0.8,
        )
        decision_event = self.reasoning_layer.record_decision(
            name="clean_decision",
            decision=decision,
        )

        # 2. Record Execution linked to Decision
        execution_event = self.reasoning_layer.record_execution(
            name="clean_execution",
            decision_event_id=decision_event.event_id,
            outputs={"cleaned": True},
        )

        self.assertEqual(execution_event.parent_event_id, decision_event.event_id)
        events = self.store.get(self.context.trace_id)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], decision_event)
        self.assertEqual(events[1], execution_event)


if __name__ == "__main__":
    unittest.main()
