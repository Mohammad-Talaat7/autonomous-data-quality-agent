from adqa.trace.audit.summarizer import TraceSummarizer
from adqa.trace.context import TraceContext
from adqa.trace.enums import TraceComponent, TraceEventType, TraceSeverity
from adqa.trace.events import TraceEvent
from adqa.trace.reasoning import ReasonCode, ReasoningTraceEvent
from adqa.trace.store.inmemory_store import InMemoryTraceStore


class TestTraceSummarizer:
    def test_generate_report_basic(self):
        store = InMemoryTraceStore()
        context = TraceContext()
        trace_id = context.trace_id

        # Root event
        root_event = TraceEvent(
            trace_id=trace_id,
            name="Workflow Start",
            component=TraceComponent.TRACE,
            event_type=TraceEventType.START,
        )
        store.append(root_event)

        # Rule check event (child of root)
        rule_event = TraceEvent(
            trace_id=trace_id,
            parent_event_id=root_event.event_id,
            name="Null Check",
            component=TraceComponent.RULE,
            event_type=TraceEventType.CHECK,
            inputs={"column": "email"},
            outputs={"passed": False, "failed_rows": 10},
            severity=TraceSeverity.WARNING,
        )
        store.append(rule_event)

        # Decision event (child of rule)
        decision_event = ReasoningTraceEvent(
            trace_id=trace_id,
            parent_event_id=rule_event.event_id,
            name="Quarantine Data",
            execution_event_id=rule_event.event_id,
            confidence=0.95,
            reasons=[ReasonCode.HIGH_NULL_RATIO],
            evidence={"ratio": 0.5},
        )
        store.append(decision_event)

        # Error event
        error_event = TraceEvent(
            trace_id=trace_id,
            parent_event_id=root_event.event_id,
            name="Upload Failed",
            component=TraceComponent.TRACE,
            event_type=TraceEventType.ERROR,
            severity=TraceSeverity.ERROR,
            metadata={"error_message": "Connection timeout"},
        )
        store.append(error_event)

        summarizer = TraceSummarizer(store)
        report = summarizer.generate_report(context)
        print(report)

        # Assertions
        assert f"Trace ID: {trace_id}" in report

        # Check Issue Summary
        assert "⚠️  ISSUE SUMMARY" in report
        assert "⚠️ WARNING" in report
        assert "Null Check" in report
        assert "❌ ERROR" in report
        assert "Upload Failed" in report

        # Check Narrative and Formatting
        assert "📜 EXECUTION LOG" in report
        assert "[TRACE] Workflow Start (start)" in report
        assert "Rule 'Null Check': FAILED" in report
        assert "{'passed': False, 'failed_rows': 10}" in report
        assert "Decision 'Quarantine Data' (Confidence: 0.95)." in report
        assert "Reasons: high_null_ratio. Evidence: {'ratio': 0.5}" in report
        assert "ERROR in 'Upload Failed': Connection timeout" in report

        # Check indentation
        _, execution_log = report.split("📜 EXECUTION LOG")
        log_lines = [log for log in execution_log.splitlines() if log.strip()]

        # root is log_lines[0]
        # rule is log_lines[1]
        # decision is log_lines[2]
        # error is log_lines[3]

        assert log_lines[1].startswith("  [")
        assert log_lines[2].startswith("    [")
        assert log_lines[3].startswith("  [")

    def test_empty_trace(self):
        store = InMemoryTraceStore()
        context = TraceContext()
        summarizer = TraceSummarizer(store)
        report = summarizer.generate_report(context)
        assert f"No events found for trace {context.trace_id}" == report

    def test_fix_proposal_template(self):
        store = InMemoryTraceStore()
        context = TraceContext()
        trace_id = context.trace_id

        event = TraceEvent(
            trace_id=trace_id,
            name="Impute Mean",
            component=TraceComponent.FIX,
            event_type=TraceEventType.PROPOSAL,
            outputs={"sql": "UPDATE table SET col = 0"},
            metadata={"strategy": "mean_imputation"},
        )
        store.append(event)

        summarizer = TraceSummarizer(store)
        report = summarizer.generate_report(context)

        assert "Proposed Fix 'Impute Mean' using strategy 'mean_imputation'." in report
        assert "Details: {'sql': 'UPDATE table SET col = 0'}" in report
