from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import UUID

from adqa.trace.context import TraceContext
from adqa.trace.emitter import TraceEmitter
from adqa.trace.enums import TraceComponent, TraceEventType, TraceSeverity
from adqa.trace.events import TraceEvent


@dataclass(frozen=True)
class DecisionRecord:
    """
    Structured representation of an LLM decision.
    """

    decision_type: str
    rationale: str
    confidence_score: float
    alternatives_considered: list[str] = field(default_factory=list)
    model_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LLMReasoningLayer:
    """
    Layer responsible for LLM reasoning and capturing decisions as trace events.
    """

    def __init__(self, context: TraceContext, emitter: TraceEmitter) -> None:
        self._context = context
        self._emitter = emitter

    def record_decision(
        self,
        name: str,
        decision: DecisionRecord,
        inputs: dict[str, Any] | None = None,
        parent_event_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """
        Records a decision made by the reasoning layer.

        Args:
            name: Name of the decision point.
            decision: The structured decision record.
            inputs: The inputs that led to this decision.
            parent_event_id: Optional ID of the parent event.
            metadata: Optional additional metadata.

        Returns:
            The created TraceEvent.
        """
        event = TraceEvent(
            trace_id=self._context.trace_id,
            parent_event_id=parent_event_id,
            component=TraceComponent.DECISION,
            event_type=TraceEventType.DECISION,
            severity=TraceSeverity.INFO,
            name=name,
            inputs=inputs,
            outputs=decision.to_dict(),
            metadata=metadata or {},
        )
        self._emitter.emit(event)
        return event

    def record_execution(
        self,
        name: str,
        decision_event_id: UUID,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        component: TraceComponent = TraceComponent.FIX,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """
        Records an execution event that was triggered by a decision.

        Args:
            name: Name of the execution step.
            decision_event_id: Decision event ID authorizing the execution.
            inputs: Inputs to the execution.
            outputs: Outputs of the execution.
            component: The component performing the execution.
            metadata: Optional additional metadata.

        Returns:
            The created TraceEvent.
        """
        event = TraceEvent(
            trace_id=self._context.trace_id,
            parent_event_id=decision_event_id,
            component=component,
            event_type=TraceEventType.RESULT,
            severity=TraceSeverity.INFO,
            name=name,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata or {},
        )
        self._emitter.emit(event)
        return event
