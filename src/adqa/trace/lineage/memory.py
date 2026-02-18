# adqa/trace/lineage/memory.py

from collections import defaultdict
from uuid import UUID

from .adapter import LineageAdapter
from .model import LineageNode


class InMemoryLineageAdapter(LineageAdapter):
    """
    In-memory lineage adapter.
    Intended for Phase-2, testing, and debugging.
    """

    def __init__(self) -> None:
        self._nodes: defaultdict[UUID, list[LineageNode]] = defaultdict(list)

    def start_trace(self, trace_id: UUID) -> None:
        self._nodes.setdefault(trace_id, [])

    def record(self, node: LineageNode) -> None:
        self._nodes[node.trace_id].append(node)

    def get(self, trace_id: UUID) -> list[LineageNode]:
        return list(self._nodes.get(trace_id, []))
