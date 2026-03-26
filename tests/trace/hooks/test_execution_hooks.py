# tests/trace/hooks/test_execution_hooks.py

from adqa.trace.context import TraceContext
from adqa.trace.emitter import TraceEmitter
from adqa.trace.hooks.context import reset_current_emitter, set_current_emitter
from adqa.trace.hooks.decorators import trace_fix, trace_metric, trace_rule
from adqa.trace.store.inmemory_store import InMemoryTraceStore


class TestExecutionHooks:
    def test_trace_metric_captures_output(self) -> None:
        store = InMemoryTraceStore()
        context = TraceContext()
        emitter = TraceEmitter(context, store=store, store_traces=True)

        token = set_current_emitter(emitter)
        try:

            @trace_metric()
            def add(a, b):
                return a + b

            result = add(2, 3)
            assert result == 5

            events = store.get(context.trace_id)
            # Filter for the success event
            success_events = [e for e in events if e.name == "metric.add.success"]
            start_events = [e for e in events if e.name == "metric.add"]

            assert len(success_events) == 1
            evt = success_events[0]
            assert evt.outputs == {"result": 5}

            assert len(start_events) == 1
            start_evt = start_events[0]
            assert start_evt.inputs is not None
            assert start_evt.inputs["args"] == [2, 3]

        finally:
            reset_current_emitter(token)

    def test_trace_rule_captures_output(self) -> None:
        store = InMemoryTraceStore()
        context = TraceContext()
        emitter = TraceEmitter(context, store=store, store_traces=True)

        token = set_current_emitter(emitter)
        try:

            @trace_rule()
            def check_positive(x):
                return x > 0

            assert check_positive(10) is True

            events = store.get(context.trace_id)
            success_events = [
                e for e in events if e.name == "rule.check_positive.success"
            ]
            assert len(success_events) == 1
            evt = success_events[0]
            assert evt.outputs == {"result": True}

        finally:
            reset_current_emitter(token)

    def test_trace_fix_captures_output(self) -> None:
        store = InMemoryTraceStore()
        context = TraceContext()
        emitter = TraceEmitter(context, store=store, store_traces=True)

        token = set_current_emitter(emitter)
        try:

            @trace_fix()
            def propose_fix(val):
                return {"action": "replace", "value": val}

            _ = propose_fix("new_val")

            events = store.get(context.trace_id)
            success_events = [e for e in events if e.name == "fix.propose_fix.success"]
            assert len(success_events) == 1
            evt = success_events[0]
            # to_trace_primitive handles dicts if they contain primitives
            assert evt.outputs == {"result": {"action": "replace", "value": "new_val"}}

        finally:
            reset_current_emitter(token)
