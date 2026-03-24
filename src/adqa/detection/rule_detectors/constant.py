# constant.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class ConstantColumnDetector(ColumnDetector):
    name = "ConstantColumnDetector"
    dimension = QualityDimension.UNIQUENESS

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.constant_column_threshold if thresholds else 1

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        unique = getattr(profile, "unique_count", None)

        if unique == self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="constant_column",
                    column=column,
                    severity_hint=1.0,
                    metrics={"observed_value": unique, "threshold": self.threshold},
                    description=f"{column} is constant (unique count: {unique})",
                )
            ]
        return []
