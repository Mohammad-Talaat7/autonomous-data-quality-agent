# type_mismatch.py

import pandas as pd

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

        # 1. Numeric check for physical numeric types
        if "int" in physical_dtype.lower() or "float" in physical_dtype.lower():
            if logical_type not in ["numeric", "boolean", "datetime"]:
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

        # 2. Heuristic check for 'object' types that should be numeric
        elif "object" in physical_dtype.lower() and context.raw_data_sample is not None:
            series = context.raw_data_sample[column].dropna()
            if not series.empty:
                # Try converting to numeric
                numeric_conv = pd.to_numeric(series, errors="coerce")
                valid_numeric_ratio = numeric_conv.notna().mean()

                # If more than 80% are valid numbers, it should probably be numeric
                if valid_numeric_ratio > 0.8:
                    return [
                        DetectionResult(
                            detector_name=self.name,
                            issue_type="type_mismatch",
                            column=column,
                            severity_hint=0.7,
                            metrics={"valid_numeric_ratio": valid_numeric_ratio},
                            description=(
                                f"{column} is stored as {physical_dtype} but "
                                f"{valid_numeric_ratio:.0%} of values are "
                                "numeric. Should be cast to numeric."
                            ),
                        )
                    ]

        return []
