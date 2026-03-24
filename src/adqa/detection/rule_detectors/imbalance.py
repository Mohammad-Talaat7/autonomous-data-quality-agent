# imbalance.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class ImbalanceDetector(ColumnDetector):
    name = "ImbalanceDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.imbalance_threshold if thresholds else 0.9

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        dist = getattr(profile, "value_distribution", None)

        if not dist:
            return []

        max_ratio = max(dist.values())

        if max_ratio > self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="imbalance",
                    column=column,
                    severity_hint=max_ratio,
                    metrics={"observed_value": max_ratio, "threshold": self.threshold},
                    description=f"{column} is highly imbalanced ({max_ratio:.2%})",
                )
            ]
        return []
