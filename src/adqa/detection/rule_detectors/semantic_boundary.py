from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class SemanticBoundaryDetector(ColumnDetector):
    """
    Detects values that violate semantic boundaries
    (e.g. negative prices, unrealistic ages).
    """

    name = "SemanticBoundaryDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.boundaries = {
            "age": (0, 125),
            "price": (0, float("inf")),
            "count": (0, float("inf")),
            "percentage": (0, 100),
            "probability": (0, 1),
        }

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        profile = context.get_column(column)

        # Check if we have semantic info
        semantic_label = ""
        if context.ml_profiles:
            for ml in context.ml_profiles:
                if ml.target == column and ml.model_name == "semantic_classifier":
                    label = ml.outputs.get("predicted_class", "").lower()
                    if label in self.boundaries:
                        semantic_label = label
                        break

        if not semantic_label:
            # Fallback to name-based heuristic
            for key in self.boundaries:
                if key in column.lower():
                    semantic_label = key
                    break

        if not semantic_label or semantic_label not in self.boundaries:
            return []

        # Check numeric boundaries
        if hasattr(profile, "numeric_metrics") and profile.numeric_metrics:
            min_val = profile.numeric_metrics.min
            max_val = profile.numeric_metrics.max

            b_min, b_max = self.boundaries[semantic_label]

            results = []
            if min_val < b_min:
                results.append(
                    DetectionResult(
                        detector_name=self.name,
                        issue_type="semantic_violation",
                        column=column,
                        severity_hint=1.0,
                        metrics={
                            "observed_min": min_val,
                            "boundary_min": b_min,
                            "semantic": semantic_label,
                        },
                        description=(
                            f"{column} ({semantic_label}) has values "
                            f"below logical minimum {b_min}"
                        ),
                    )
                )

            if max_val > b_max:
                results.append(
                    DetectionResult(
                        detector_name=self.name,
                        issue_type="semantic_violation",
                        column=column,
                        severity_hint=1.0,
                        metrics={
                            "observed_max": max_val,
                            "boundary_max": b_max,
                            "semantic": semantic_label,
                        },
                        description=(
                            f"{column} ({semantic_label}) has values "
                            f"above logical maximum {b_max}"
                        ),
                    )
                )

            return results

        return []
