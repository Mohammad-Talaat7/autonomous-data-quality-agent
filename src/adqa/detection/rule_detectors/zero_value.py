# zero_value.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, QualityDimension
from ..context import DetectionContext
from ..results import DetectionResult


class ZeroValueDetector(ColumnDetector):
    name = "ZeroValueDetector"
    dimension = QualityDimension.COMPLETENESS

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.zero_value_ratio_threshold if thresholds else 0.3

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        metrics = getattr(profile, "numeric_metrics", None)

        if not metrics:
            return []

        ratio = getattr(metrics, "zero_ratio", 0.0)

        if ratio > self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="zero_value",
                    column=column,
                    severity_hint=min(ratio, 1.0),
                    metrics={
                        "observed_value": ratio,
                        "threshold": self.threshold,
                    },
                    description=f"{column} has {ratio:.2%} zero values"
                    + f" (threshold: {self.threshold:.2%})",
                )
            ]
        return []
