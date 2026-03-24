# detection/context.py

from dataclasses import dataclass
from typing import Any


@dataclass
class DetectionContext:
    """
    Unified input context for all detectors.
    """

    dataset_profile: Any
    column_profiles: dict[str, Any]

    ml_profiles: Any | None = None

    correlation_matrix: Any | None = None
    historical_profiles: Any | None = None
    raw_data_sample: Any | None = None  # for regex / temporal checks

    # Optional future extensions
    metadata: dict[str, Any] | None = None

    def get_column(self, column: str) -> Any:
        return self.column_profiles.get(column)

    def has_ml(self) -> bool:
        return self.ml_profiles is not None
