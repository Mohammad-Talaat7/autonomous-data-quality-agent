# src/adqa/trace/lineage/adapter.py

from abc import ABC, abstractmethod
from typing import Iterable
from uuid import UUID

from adqa.trace.lineage.model import LineageNode


class LineageAdapter(ABC):
    """
    Abstract interface for lineage tracking backends.
    """

    @abstractmethod
    def start_trace(self, trace_id: UUID) -> None:
        """
        Initialize lineage tracking for a trace.
        """

    @abstractmethod
    def record(self, node: LineageNode) -> None:
        """
        Record a lineage node.
        """

    @abstractmethod
    def get(self, trace_id: UUID) -> Iterable[LineageNode]:
        """
        Retrieve lineage nodes for a trace.
        """
