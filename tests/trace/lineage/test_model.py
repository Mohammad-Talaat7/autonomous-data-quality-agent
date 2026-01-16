from datetime import UTC, datetime
from uuid import UUID

from adqa.trace.lineage.model import LineageNode


def test_lineage_node_creation() -> None:
    operation = "test_op"
    inputs = ["in1"]
    outputs = ["out1"]
    node = LineageNode(operation=operation, inputs=inputs, outputs=outputs)

    assert node.operation == operation
    assert node.inputs == inputs
    assert node.outputs == outputs
    assert isinstance(node.node_id, UUID)
    assert isinstance(node.trace_id, UUID)
    assert node.metadata == {}
    assert isinstance(node.timestamp, datetime)
    assert node.timestamp.tzinfo == UTC


def test_lineage_node_custom_values() -> None:
    node_id = UUID("00000000-0000-0000-0000-000000000001")
    trace_id = UUID("00000000-0000-0000-0000-000000000002")
    metadata = {"key": "value"}

    node = LineageNode(
        operation="op",
        inputs=["in"],
        outputs=["out"],
        node_id=node_id,
        trace_id=trace_id,
        metadata=metadata,
    )

    assert node.node_id == node_id
    assert node.trace_id == trace_id
    assert node.metadata == metadata
