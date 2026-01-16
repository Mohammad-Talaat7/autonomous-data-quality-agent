from uuid import uuid4
from adqa.trace.lineage.memory import InMemoryLineageAdapter
from adqa.trace.lineage.model import LineageNode

def test_in_memory_adapter_record_and_get() -> None:
    adapter = InMemoryLineageAdapter()
    trace_id = uuid4()
    node = LineageNode(
        operation="op",
        inputs=["in"],
        outputs=["out"],
        trace_id=trace_id
    )
    
    adapter.start_trace(trace_id)
    adapter.record(node)
    
    nodes = adapter.get(trace_id)
    assert len(nodes) == 1
    assert nodes[0] == node

def test_in_memory_adapter_multiple_traces() -> None:
    adapter = InMemoryLineageAdapter()
    t1 = uuid4()
    t2 = uuid4()
    
    n1 = LineageNode(operation="op1", inputs=[], outputs=[], trace_id=t1)
    n2 = LineageNode(operation="op2", inputs=[], outputs=[], trace_id=t2)
    
    adapter.record(n1)
    adapter.record(n2)
    
    assert adapter.get(t1) == [n1]
    assert adapter.get(t2) == [n2]

def test_in_memory_adapter_empty_get() -> None:
    adapter = InMemoryLineageAdapter()
    assert adapter.get(uuid4()) == []
