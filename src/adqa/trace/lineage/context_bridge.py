from collections.abc import Generator
from contextlib import contextmanager

from ..emitter import TraceEmitter
from ..enums import TraceValue
from ..hooks.context import get_current_emitter
from ..hooks.lineage_context import (
    get_current_lineage_recorder,
    reset_current_lineage_recorder,
    set_current_lineage_recorder,
)
from .context import LineageStepContext, lineage_step
from .recorder import LineageRecorder


@contextmanager
def lineage_hook(
    *,
    lineage: LineageRecorder | None,
    emitter: TraceEmitter | None,
    operation: str,
    inputs: TraceValue | None = None,
    outputs: TraceValue | None = None,
    metadata: dict[str, TraceValue] | None = None,
) -> Generator[LineageStepContext | None, None, None]:
    """
    Lineage hook that mirrors execution_hook semantics.
    """
    if lineage is None:
        lineage = get_current_lineage_recorder()

    if emitter is None:
        emitter = get_current_emitter()

    if lineage is None or emitter is None:
        yield None
        return

    token = set_current_lineage_recorder(lineage)
    try:
        with lineage_step(
            lineage,
            trace_id=emitter.context.trace_id,
            operation=operation,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata,
        ) as ctx:
            yield ctx
    finally:
        reset_current_lineage_recorder(token)
