# pii.py

from typing import Any

from ..base import BaseMLDetector, DetectionContext, QualityDimension
from ..results import MLEvidence


class PIIDetector(BaseMLDetector):
    name = "PIIDetector"
    dimension = QualityDimension.INTEGRITY  # PII is an integrity/security risk

    def __init__(self, **kwargs: Any) -> None:
        pass

    def run_model(self, context: DetectionContext) -> list[MLEvidence]:
        ml_profiles = context.ml_profiles
        if not ml_profiles:
            return []

        results = []
        pii_types = {"email", "phone", "ssn", "credit_card", "address", "name"}

        for ml in ml_profiles:
            if ml.model_name == "SemanticClassifier":
                label = ml.outputs.get("label")
                confidence = ml.outputs.get("confidence", 0.0)

                if label in pii_types and confidence > 0.6:
                    results.append(
                        MLEvidence(
                            model_name=self.name,
                            signal_type="pii_detected",
                            column=ml.target,
                            score=confidence,
                            confidence=0.9,
                            metadata={"pii_type": label},
                        )
                    )
        return results
