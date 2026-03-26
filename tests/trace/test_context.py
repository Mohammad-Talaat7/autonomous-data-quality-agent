# tests/trace/test_context.py

from __future__ import annotations

import unittest
from datetime import datetime
from uuid import UUID, uuid4

from adqa.trace.context import TraceContext


class TestTraceContext(unittest.TestCase):
    def test_default_creation(self) -> None:
        """Test that a TraceContext can be created with default values."""
        context = TraceContext()
        self.assertIsInstance(context.trace_id, UUID)
        self.assertIsNone(context.dataset_id)
        self.assertIsNone(context.parent_trace_id)
        self.assertEqual(context.mode, "advisory")
        self.assertIsInstance(context.created_at, datetime)

    def test_creation_with_values(self) -> None:
        """Test that a TraceContext can be created with specified values."""
        trace_id = uuid4()
        parent_trace_id = uuid4()
        created_at = datetime.now()
        context = TraceContext(
            trace_id=trace_id,
            dataset_id="my-dataset",
            parent_trace_id=parent_trace_id,
            mode="execution",
            created_at=created_at,
        )
        self.assertEqual(context.trace_id, trace_id)
        self.assertEqual(context.dataset_id, "my-dataset")
        self.assertEqual(context.parent_trace_id, parent_trace_id)
        self.assertEqual(context.mode, "execution")
        self.assertEqual(context.created_at, created_at)

    def test_to_dict(self) -> None:
        """Test that the to_dict method returns the correct dictionary."""
        trace_id = uuid4()
        parent_trace_id = uuid4()
        created_at = datetime.now()
        context = TraceContext(
            trace_id=trace_id,
            dataset_id="my-dataset",
            parent_trace_id=parent_trace_id,
            mode="execution",
            created_at=created_at,
        )
        context_dict = context.to_dict()
        self.assertEqual(context_dict["trace_id"], str(trace_id))
        self.assertEqual(context_dict["dataset_id"], "my-dataset")
        self.assertEqual(context_dict["parent_trace_id"], str(parent_trace_id))
        self.assertEqual(context_dict["mode"], "execution")
        self.assertEqual(context_dict["created_at"], created_at.isoformat())

    def test_to_dict_with_none(self) -> None:
        """Test that the to_dict method handles None values correctly."""
        context = TraceContext()
        context_dict = context.to_dict()
        self.assertIsInstance(context_dict["trace_id"], str)
        self.assertIsNone(context_dict["dataset_id"])
        self.assertIsNone(context_dict["parent_trace_id"])
        self.assertEqual(context_dict["mode"], "advisory")
        self.assertIsInstance(context_dict["created_at"], str)


if __name__ == "__main__":
    _ = unittest.main()
