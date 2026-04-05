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

        # In ADQA, mode_ratio in categorical_metrics indicates the
        # dominance of the top class
        ratio = 0.0
        if hasattr(profile, "categorical_metrics") and profile.categorical_metrics:
            ratio = profile.categorical_metrics.mode_ratio
        else:
            # Fallback to general attribute
            ratio = getattr(profile, "mode_ratio", 0.0)

        if ratio > self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="imbalance",
                    column=column,
                    severity_hint=ratio,
                    metrics={"observed_value": ratio, "threshold": self.threshold},
                    description=f"{column} is highly imbalanced ({ratio:.2%})",
                )
            ]
        return []
