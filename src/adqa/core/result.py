# adqa/result.py

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from ..profiling.models.profiling_result import ProfilingResult


@dataclass(frozen=True)
class ADQAResult:
    """
    Public result object returned by ADQA.analyze().
    """

    # Core outputs
    dataframe: pd.DataFrame | None

    # Phase 3
    profiles: ProfilingResult | None = None
    detections: Any | None = None
    scores: Any | None = None
    decision: Any | None = None

    # Execution semantics
    execution_mode: str | None = None
    actions: list[Any] | None = None

    # Trace references (never raw trace data)
    trace_id: str | None = None
    config_hash: str | None = None

    # Error handling
    error: str | None = None
