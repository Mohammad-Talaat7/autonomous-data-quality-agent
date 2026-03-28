# skewness.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, QualityDimension
from ..context import DetectionContext
from ..results import DetectionResult


class SkewnessDetector(ColumnDetector):
    name = "SkewnessDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.skewness_threshold if thresholds else 1.0

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        skew = getattr(profile, "skewness", None)

        if skew and abs(skew) > self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="skewed_distribution",
                    column=column,
                    severity_hint=min(abs(skew) / 10, 1.0),
                    metrics={"observed_value": skew, "threshold": self.threshold},
                    description=f"{column} is highly skewed ({skew:.2f})",
                )
            ]
        return []
