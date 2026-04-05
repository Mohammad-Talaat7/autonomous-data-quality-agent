# outlier.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class OutlierDetector(ColumnDetector):
    name = "OutlierDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.outlier_ratio_threshold if thresholds else 0.05

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        metrics = getattr(profile, "behavioral_metrics", None)

        if not metrics:
            return []

        ratio = getattr(metrics, "outlier_ratio", 0.0)

        if ratio > self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="outliers",
                    column=column,
                    severity_hint=ratio,
                    metrics={"observed_value": ratio, "threshold": self.threshold},
                    description=f"{column} has {ratio:.2%} outliers"
                    + " (threshold: {self.threshold:.2%})",
                )
            ]
        return []
