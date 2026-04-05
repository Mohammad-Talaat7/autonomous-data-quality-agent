# missing.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class MissingValuesDetector(ColumnDetector):
    name = "MissingValuesDetector"
    dimension = QualityDimension.COMPLETENESS

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.missing_values_threshold if thresholds else 0.2

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)

        ratio = 0.0
        if hasattr(profile, "structural_metrics") and profile.structural_metrics:
            ratio = profile.structural_metrics.null_ratio
        else:
            ratio = getattr(profile, "null_ratio", 0.0)

        if ratio > self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="missing_values",
                    column=column,
                    severity_hint=ratio,
                    metrics={"observed_value": ratio, "threshold": self.threshold},
                    description=f"{column} has {ratio:.2%} missing values"
                    + f" (threshold: {self.threshold:.2%})",
                )
            ]
        return []
