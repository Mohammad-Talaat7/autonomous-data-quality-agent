# type_mismatch.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, QualityDimension
from ..context import DetectionContext
from ..results import DetectionResult


class TypeMismatchDetector(ColumnDetector):
    name = "TypeMismatchDetector"
    dimension = QualityDimension.INTEGRITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        pass

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        physical_dtype = profile.dtype
        logical_type = profile.logical_type

        # Basic check: if physical is object but it was inferred as something else
        # it might be okay, but if it was inferred as UNKNOWN, it's a risk.
        if logical_type == "unknown":
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="unknown_logical_type",
                    column=column,
                    severity_hint=0.5,
                    description=f"{column} (dtype: {physical_dtype})"
                    + " has unknown logical type",
                )
            ]

        # Numeric checks
        if "int" in physical_dtype.lower() or "float" in physical_dtype.lower():
            if logical_type not in ["numeric", "boolean"]:
                return [
                    DetectionResult(
                        detector_name=self.name,
                        issue_type="type_mismatch",
                        column=column,
                        severity_hint=0.8,
                        description=f"{column} is physically {physical_dtype}"
                        + f" but inferred as {logical_type}",
                    )
                ]

        return []
