# src/adqa/trace/lineage/context.py

from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from adqa.trace.enums import TraceValue
from adqa.trace.lineage.recorder import LineageRecorder


@contextmanager
def lineage_step(
    recorder: LineageRecorder,
    *,
    trace_id: UUID,
    operation: str,
    inputs: list[str],
    outputs: list[str],
    metadata: dict[str, TraceValue] | None = None,
) -> Generator[None, None, None]:
    """
    Context manager for automatic lineage recording
    around a data transformation.
    """
    yield
    recorder.record(
        trace_id=trace_id,
        operation=operation,
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
    )
