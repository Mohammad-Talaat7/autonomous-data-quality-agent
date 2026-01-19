from adqa.trace.context import TraceContext
from adqa.trace.emitter import TraceEmitter
from adqa.trace.hooks.context import reset_current_emitter, set_current_emitter
from adqa.trace.hooks.decorators import trace_lineage
from adqa.trace.hooks.lineage_context import (
    reset_current_lineage_recorder,
    set_current_lineage_recorder,
)
from adqa.trace.lineage.memory import InMemoryLineageAdapter
from adqa.trace.lineage.recorder import LineageRecorder
from adqa.trace.store.inmemory_store import InMemoryTraceStore


class TestLineageHooks:
    def test_trace_lineage_implicit_context(self) -> None:
        store = InMemoryTraceStore()
        context = TraceContext()
        emitter = TraceEmitter(context, store=store, store_traces=True)

        lineage_adapter = InMemoryLineageAdapter()
        lineage_recorder = LineageRecorder(adapter=lineage_adapter, enabled=True)
        lineage_recorder.start_trace(context.trace_id)

        t1 = set_current_emitter(emitter)
        t2 = set_current_lineage_recorder(lineage_recorder)

        try:

            @trace_lineage(operation="test_op")
            def my_func(a, b):
                return a + b

            result = my_func(1, 2)
            assert result == 3

            nodes = lineage_recorder.get(context.trace_id)
            assert len(nodes) == 1
            assert nodes[0].operation == "test_op"
            assert nodes[0].inputs == {"args": [1, 2], "kwargs": {}}

        finally:
            reset_current_emitter(t1)
            reset_current_lineage_recorder(t2)

    def test_trace_lineage_explicit_args(self) -> None:
        store = InMemoryTraceStore()
        context = TraceContext()
        emitter = TraceEmitter(context, store=store, store_traces=True)

        lineage_adapter = InMemoryLineageAdapter()
        lineage_recorder = LineageRecorder(adapter=lineage_adapter, enabled=True)
        lineage_recorder.start_trace(context.trace_id)

        # No implicit context

        @trace_lineage(emitter=emitter, lineage=lineage_recorder)
        def my_func(a):
            return a * 2

        result = my_func(10)
        assert result == 20

    def test_trace_lineage_output_and_metadata(self) -> None:
        store = InMemoryTraceStore()
        context = TraceContext()
        emitter = TraceEmitter(context, store=store, store_traces=True)

        lineage_adapter = InMemoryLineageAdapter()
        lineage_recorder = LineageRecorder(adapter=lineage_adapter, enabled=True)
        lineage_recorder.start_trace(context.trace_id)

        t1 = set_current_emitter(emitter)
        t2 = set_current_lineage_recorder(lineage_recorder)

        try:

            @trace_lineage(metadata={"env": "test"}, capture_output=True)
            def compute_val(x):
                return x + 10

            result = compute_val(5)
            assert result == 15

            nodes = lineage_recorder.get(context.trace_id)
            assert len(nodes) == 1
            node = nodes[0]

            assert node.metadata == {"env": "test"}
            assert node.outputs == 15

        finally:
            reset_current_emitter(t1)
            reset_current_lineage_recorder(t2)
