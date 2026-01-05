from uuid import uuid4

from adqa.trace.events import TraceEvent
from adqa.trace.store.inmemory_store import InMemoryTraceStore


class TestInMemoryTraceStore:
    def test_append_and_get(self):
        store = InMemoryTraceStore()
        trace_id = uuid4()

        event1 = TraceEvent(trace_id=trace_id, name="event1")
        event2 = TraceEvent(trace_id=trace_id, name="event2")

        store.append(event1)
        store.append(event2)

        events = store.get(trace_id)
        assert len(events) == 2
        assert events[0] == event1
        assert events[1] == event2

    def test_get_empty(self):
        store = InMemoryTraceStore()
        trace_id = uuid4()
        assert store.get(trace_id) == []

    def test_trace_isolation(self):
        store = InMemoryTraceStore()
        trace_id_1 = uuid4()
        trace_id_2 = uuid4()

        event1 = TraceEvent(trace_id=trace_id_1, name="t1_e1")
        event2 = TraceEvent(trace_id=trace_id_2, name="t2_e1")

        store.append(event1)
        store.append(event2)

        events1 = store.get(trace_id_1)
        assert len(events1) == 1
        assert events1[0] == event1

        events2 = store.get(trace_id_2)
        assert len(events2) == 1
        assert events2[0] == event2
