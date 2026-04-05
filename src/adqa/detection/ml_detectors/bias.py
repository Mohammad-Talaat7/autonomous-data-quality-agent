from typing import Any

from ..base import BaseMLDetector, DetectionContext, QualityDimension
from ..results import MLEvidence


class BiasDetector(BaseMLDetector):
    """
    Detects potential bias in sensitive columns based on class imbalance.
    """

    name = "BiasDetector"
    dimension = QualityDimension.BIAS

    def __init__(self, imbalance_threshold: float = 0.9, **kwargs: Any) -> None:
        self.imbalance_threshold = imbalance_threshold

    def run_model(self, context: DetectionContext) -> list[MLEvidence]:
        results = []

        # We look for columns that might be sensitive (gender, race, age, etc.)
        # based on semantic classification or column name
        sensitive_keywords = {
            "gender",
            "sex",
            "race",
            "ethnicity",
            "age",
            "religion",
            "disability",
        }

        for col_name, profile in context.column_profiles.items():
            is_sensitive = any(k in col_name.lower() for k in sensitive_keywords)

            # Also check semantic labels if available
            if not is_sensitive and context.ml_profiles:
                for ml in context.ml_profiles:
                    if ml.target == col_name and ml.model_name == "semantic_classifier":
                        label = ml.outputs.get("predicted_class")
                        if label in sensitive_keywords:
                            is_sensitive = True
                            break

            if not is_sensitive:
                continue

            # Check for imbalance
            # We use categorical_metrics if available
            mode_ratio = 0.0
            if hasattr(profile, "categorical_metrics") and profile.categorical_metrics:
                mode_ratio = profile.categorical_metrics.mode_ratio
            else:
                mode_ratio = getattr(profile, "mode_ratio", 0.0)

            if mode_ratio > self.imbalance_threshold:
                results.append(
                    MLEvidence(
                        model_name=self.name,
                        signal_type="potential_bias",
                        column=col_name,
                        score=mode_ratio,
                        confidence=0.8,
                        metadata={
                            "reason": "Extreme class imbalance in sensitive column",
                            "mode_ratio": mode_ratio,
                            "threshold": self.imbalance_threshold,
                        },
                    )
                )

        return results
