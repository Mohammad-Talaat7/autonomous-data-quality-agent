# range.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class RangeDetector(ColumnDetector):
    name = "RangeDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.min_value = thresholds.min_value if thresholds else None
        self.max_value = thresholds.max_value if thresholds else None

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        metrics = getattr(profile, "numeric_metrics", None)

        if not metrics:
            return []

        results = []
        if self.min_value is not None and metrics.min < self.min_value:
            results.append(
                DetectionResult(
                    detector_name=self.name,
                    issue_type="range_violation_min",
                    column=column,
                    severity_hint=1.0,
                    metrics={
                        "observed_value": metrics.min,
                        "threshold": self.min_value,
                    },
                    description=f"{column} min value {metrics.min}"
                    + " is below threshold {self.min_value}",
                )
            )

        if self.max_value is not None and metrics.max > self.max_value:
            results.append(
                DetectionResult(
                    detector_name=self.name,
                    issue_type="range_violation_max",
                    column=column,
                    severity_hint=1.0,
                    metrics={
                        "observed_value": metrics.max,
                        "threshold": self.max_value,
                    },
                    description=f"{column} max value {metrics.max}"
                    + " is above threshold {self.max_value}",
                )
            )

        return results
