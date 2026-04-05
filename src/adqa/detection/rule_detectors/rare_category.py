# rare_category.py

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, QualityDimension
from ..context import DetectionContext
from ..results import DetectionResult


class RareCategoryDetector(ColumnDetector):
    name = "RareCategoryDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.rare_category_threshold if thresholds else 0.01

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)
        metrics = getattr(profile, "categorical_metrics", None)

        if not metrics:
            return []

        rare_categories = getattr(metrics, "rare_categories", [])

        if rare_categories:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="rare_category",
                    column=column,
                    severity_hint=0.5,
                    metrics={
                        "rare_categories": rare_categories,
                        "threshold": self.threshold,
                    },
                    description=f"{column} has rare categories: {rare_categories}",
                )
            ]
        return []
