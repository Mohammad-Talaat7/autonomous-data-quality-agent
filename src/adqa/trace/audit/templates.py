# adqa/trace/audit/templates.py

from __future__ import annotations

from typing import Protocol, cast

from ..enums import TraceComponent, TraceEventDict, TraceEventType


class EventTemplate(Protocol):
    def format(self, event_data: TraceEventDict) -> str: ...


class DefaultTemplate:
    def format(self, event_data: TraceEventDict) -> str:
        name = event_data.get("name", "Unknown Event")
        component = event_data.get("component", "unknown")
        event_type = event_data.get("event_type", "unknown")
        return f"[{component.upper()}] {name} ({event_type})"


class RuleCheckTemplate:
    def format(self, event_data: TraceEventDict) -> str:
        name = event_data.get("name", "Rule Check")
        inputs = event_data.get("inputs") or {}
        outputs = event_data.get("outputs") or {}
        status = "PASSED" if outputs.get("passed") else "FAILED"
        return f"Rule '{name}': {status}. Checked {inputs} -> {outputs}"


class FixProposalTemplate:
    def format(self, event_data: TraceEventDict) -> str:
        name = event_data.get("name", "Fix Proposal")
        metadata = event_data.get("metadata") or {}
        outputs = event_data.get("outputs") or {}
        strategy = metadata.get("strategy", "unknown")
        return f"Proposed Fix '{name}' using strategy '{strategy}'. Details: {outputs}"


class ErrorTemplate:
    def format(self, event_data: TraceEventDict) -> str:
        name = event_data.get("name", "Error")
        metadata = event_data.get("metadata") or {}
        error_msg = metadata.get("error_message") or "No details provided"
        return f"ERROR in '{name}': {error_msg}"


class DecisionTemplate:
    def format(self, event_data: TraceEventDict) -> str:
        name = event_data.get("name", "Decision")
        reasons = cast(list[str], event_data.get("reasons", []))
        confidence = event_data.get("confidence", 0.0)
        evidence = event_data.get("evidence", {})

        reasons_str = ", ".join(reasons) if reasons else "None"
        result = (
            f"Decision '{name}' (Confidence: {confidence:.2f}). Reasons: {reasons_str}."
        )
        result += f" Evidence: {evidence}"
        return result


# Mapping of (Component, EventType) to Template
TEMPLATE_REGISTRY: dict[tuple[str, str], EventTemplate] = {
    (TraceComponent.RULE.value, TraceEventType.CHECK.value): RuleCheckTemplate(),
    (TraceComponent.FIX.value, TraceEventType.PROPOSAL.value): FixProposalTemplate(),
    (TraceComponent.TRACE.value, TraceEventType.ERROR.value): ErrorTemplate(),
    (TraceComponent.TRACE.value, TraceEventType.DECISION.value): DecisionTemplate(),
}


def format_event(event_data: TraceEventDict) -> str:
    """
    Selects the appropriate template and formats the event data.
    """
    component = event_data.get("component")
    event_type = event_data.get("event_type")

    template = TEMPLATE_REGISTRY.get((component, event_type), DefaultTemplate())
    return template.format(event_data)
