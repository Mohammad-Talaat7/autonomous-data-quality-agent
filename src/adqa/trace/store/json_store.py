# src/adqa/trace/store/json_store.py

import json
from datetime import datetime
from pathlib import Path
from typing import cast, override
from uuid import UUID

from ..enums import TraceComponent, TraceEventDict, TraceEventType, TraceSeverity
from ..events import TraceEvent
from .base import TraceStore


class JSONTraceStore(TraceStore):
    """
    Append-only JSON Lines trace store.

    Each TraceEvent is written as one JSON object per line.
    Suitable for:
    - experiments
    - offline analysis
    - replay & auditing
    """

    def __init__(self, file_path: str | Path) -> None:
        self._path: Path = Path(file_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure file exists
        self._path.touch(exist_ok=True)

    @override
    def append(self, event: TraceEvent) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            json.dump(event.to_dict(), f)
            _ = f.write("\n")

    @override
    def get(self, trace_id: UUID) -> list[TraceEvent]:
        events: list[TraceEvent] = []

        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                data: TraceEventDict = cast(TraceEventDict, json.loads(line))
                if data.get("trace_id") == str(trace_id):
                    events.append(self._from_dict(data))

        return events

    @staticmethod
    def _from_dict(data: TraceEventDict) -> TraceEvent:
        """
        Reconstruct TraceEvent from serialized dict.
        """

        return TraceEvent(
            event_id=UUID(data["event_id"]),
            trace_id=UUID(data["trace_id"]),
            parent_event_id=(
                UUID(data["parent_event_id"]) if data["parent_event_id"] else None
            ),
            component=TraceComponent(data["component"]),
            event_type=TraceEventType(data["event_type"]),
            severity=TraceSeverity(data["severity"]),
            name=data["name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            inputs=data.get("inputs"),
            outputs=data.get("outputs"),
            metadata=data.get("metadata", {}),
        )
