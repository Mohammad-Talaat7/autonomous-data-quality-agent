# src/adqa/trace/lineage/context.py

from collections.abc import Generator
from contextlib import contextmanager
from typing import TypedDict
from uuid import UUID

from ..enums import TraceValue
from .recorder import LineageRecorder


class LineageStepContext(TypedDict):
    inputs: TraceValue | None
    outputs: TraceValue | None
    metadata: dict[str, TraceValue]


@contextmanager
def lineage_step(
    recorder: LineageRecorder,
    *,
    trace_id: UUID,
    operation: str,
    inputs: TraceValue | None,
    outputs: TraceValue | None,
    metadata: dict[str, TraceValue] | None = None,
) -> Generator[LineageStepContext, None, None]:
    """
    Context manager for automatic lineage recording
    around a data transformation.
    """
    ctx: LineageStepContext = {
        "inputs": inputs,
        "outputs": outputs,
        "metadata": metadata or {},
    }
    yield ctx
    recorder.record(
        trace_id=trace_id,
        operation=operation,
        inputs=ctx["inputs"],
        outputs=ctx["outputs"],
        metadata=ctx["metadata"],
    )
