# duplicate.py

from ...config.model import DetectionThresholds
from ..base import DatasetDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class DuplicateRowsDetector(DatasetDetector):
    name = "DuplicateRowsDetector"
    dimension = QualityDimension.UNIQUENESS

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.duplicate_rows_threshold if thresholds else 0.1

    def detect(self, context: DetectionContext) -> list[DetectionResult]:
        ratio = getattr(context.dataset_profile, "duplicate_ratio", 0)

        if ratio > self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="duplicate_rows",
                    scope="dataset",
                    severity_hint=ratio,
                    metrics={"observed_value": ratio, "threshold": self.threshold},
                    description=f"{ratio:.2%} duplicate rows"
                    + " (threshold: {self.threshold:.2%})",
                )
            ]
        return []
