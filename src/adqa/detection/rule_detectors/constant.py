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

        # In ADQA, cardinality (unique count) is in categorical_metrics
        # or can be derived from unique_ratio
        unique = 0
        mode_ratio = 0.0

        if hasattr(profile, "categorical_metrics") and profile.categorical_metrics:
            unique = profile.categorical_metrics.cardinality
            mode_ratio = profile.categorical_metrics.mode_ratio
        elif hasattr(profile, "structural_metrics") and profile.structural_metrics:
            # unique_ratio = unique_count / total_rows
            row_count = context.dataset_profile.metadata.row_count
            unique = int(round(profile.structural_metrics.unique_ratio * row_count))
            # We don't have mode_ratio in structural, so we fallback
        else:
            unique = getattr(profile, "unique_count", 0)

        is_constant = False
        if self.threshold < 1.0:
            # Ratio-based check (e.g. 99% values are the same)
            is_constant = mode_ratio >= self.threshold
            observed = mode_ratio
            desc = f"{column} is nearly constant (mode ratio: {mode_ratio:.2%})"
        else:
            # Count-based check (e.g. <= 1 unique value)
            is_constant = 0 < unique <= self.threshold
            observed = unique
            desc = f"{column} is constant (unique count: {unique})"

        if is_constant:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="constant_column",
                    column=column,
                    severity_hint=1.0,
                    metrics={"observed_value": observed, "threshold": self.threshold},
                    description=desc,
                )
            ]
        return []
