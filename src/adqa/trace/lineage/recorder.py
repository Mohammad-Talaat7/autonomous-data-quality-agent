# adqa/trace/lineage/recorder.py

from collections.abc import Iterable
from uuid import UUID

from ..enums import TraceValue
from .adapter import LineageAdapter
from .model import LineageNode


class LineageRecorder:
    """
    Coordinates lineage recording with optional enable/disable policy.
    """

    def __init__(
        self,
        adapter: LineageAdapter | None = None,
        *,
        enabled: bool = False,
    ) -> None:
        self._adapter: LineageAdapter | None = adapter
        self._enabled: bool = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        if self._adapter is None:
            raise RuntimeError("Cannot enable lineage without an adapter")
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def start_trace(self, trace_id: UUID) -> None:
        if self._enabled and self._adapter is not None:
            self._adapter.start_trace(trace_id)

    def record(
        self,
        *,
        trace_id: UUID,
        operation: str,
        inputs: TraceValue | None,
        outputs: TraceValue | None,
        metadata: dict[str, TraceValue] | None = None,
    ) -> None:
        if not self._enabled or self._adapter is None:
            return

        node = LineageNode(
            trace_id=trace_id,
            operation=operation,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata or {},
        )

        self._adapter.record(node)

    def get(self, trace_id: UUID) -> Iterable[LineageNode]:
        if self._adapter is None:
            return []
        return self._adapter.get(trace_id)
