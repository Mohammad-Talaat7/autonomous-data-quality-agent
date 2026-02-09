# adqa/trace/audit/summarizer.py

from __future__ import annotations

from dataclasses import dataclass, field

from ..context import TraceContext
from ..enums import TraceEventDict, TraceSeverity
from ..store.base import TraceStore
from .templates import format_event


@dataclass
class TraceNode:
    """A node in the trace tree for hierarchical rendering."""

    event: TraceEventDict
    children: list[TraceNode] = field(default_factory=list)


class TraceSummarizer:
    """
    Generates human-readable audit reports using hierarchical tree traversal.
    """

    def __init__(self, store: TraceStore):
        self.store: TraceStore = store

    def generate_report(self, context: TraceContext) -> str:
        """
        Creates a full text report for the given trace context.
        """
        events = list(self.store.get(context.trace_id))

        if not events:
            return f"No events found for trace {context.trace_id}"

        event_dicts = [e.to_dict() for e in events]
        roots = self._build_tree(event_dicts)

        report_lines: list[str] = []
        report_lines.append("ADQA Audit Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Trace ID: {context.trace_id}")
        report_lines.append(f"Timestamp: {context.created_at.isoformat()}")
        report_lines.append(f"Execution Mode: {context.mode}")
        if context.dataset_id:
            report_lines.append(f"Dataset ID: {context.dataset_id}")
        report_lines.append("-" * 40)
        report_lines.append("")

        # 1. Issue Summary
        issues = self.summarize_issues(event_dicts)
        if issues:
            report_lines.append("⚠️  ISSUE SUMMARY")
            report_lines.extend(issues)
            report_lines.append("")
        else:
            report_lines.append("✅ No critical issues detected.")
            report_lines.append("")

        # 2. Execution Narrative
        report_lines.append("📜 EXECUTION LOG")
        for root in roots:
            self._render_node(root, 0, report_lines)

        return "\n".join(report_lines)

    def summarize_issues(self, events: list[TraceEventDict]) -> list[str]:
        """
        Groups and formats high-severity events.
        """
        severity_map = {
            TraceSeverity.CRITICAL.value: "🔴 CRITICAL",
            TraceSeverity.ERROR.value: "❌ ERROR",
            TraceSeverity.WARNING.value: "⚠️ WARNING",
        }

        issues: list[str] = []
        # Sort by severity priority (Critical > Error > Warning)
        sorted_events = sorted(
            [e for e in events if e.get("severity") in severity_map],
            key=lambda x: (
                x.get("severity") == TraceSeverity.WARNING.value,
                x.get("timestamp", ""),
            ),
        )

        for event in sorted_events:
            severity = event["severity"]
            prefix = severity_map.get(severity, "???")
            timestamp = event.get("timestamp", "")
            msg = format_event(event)
            issues.append(f"{prefix} [{timestamp}]: {msg}")

        return issues

    def _build_tree(self, events: list[TraceEventDict]) -> list[TraceNode]:
        """
        Converts a flat list of events into a list of root nodes.
        """
        nodes = {e["event_id"]: TraceNode(event=e) for e in events}
        roots: list[TraceNode] = []

        for _, node in nodes.items():
            parent_id = node.event.get("parent_event_id")
            if parent_id and parent_id in nodes:
                nodes[parent_id].children.append(node)
            else:
                roots.append(node)
        return roots

    def _render_node(self, node: TraceNode, depth: int, lines: list[str]) -> None:
        """
        Recursively renders nodes with indentation.
        """
        indent = "  " * depth
        timestamp = node.event.get("timestamp", "")
        formatted_msg = format_event(node.event)

        lines.append(f"{indent}[{timestamp}] {formatted_msg}")

        for child in node.children:
            self._render_node(child, depth + 1, lines)

    def generate_narrative(self, events: list[TraceEventDict]) -> list[str]:
        """
        Compatibility method for getting the narrative as a list of strings.
        """
        roots = self._build_tree(events)
        lines: list[str] = []
        for root in roots:
            self._render_node(root, 0, lines)
        return lines
