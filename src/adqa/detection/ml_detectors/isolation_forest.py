# ml_detectors/isolation_forest.py

from typing import Any

try:
    from sklearn.ensemble import IsolationForest
except ImportError:
    IsolationForest = None

from ..base import BaseMLDetector, DetectionContext, QualityDimension
from ..results import MLEvidence


class IsolationForestDetector(BaseMLDetector):
    name = "IsolationForest"
    dimension = QualityDimension.ACCURACY

    def __init__(self, **kwargs: Any) -> None:
        pass

    def run_model(self, context: DetectionContext) -> list[MLEvidence]:
        if IsolationForest is None:
            # Skip if scikit-learn is not installed
            return []

        if context.raw_data_sample is None:
            return []

        df = context.raw_data_sample.select_dtypes(include="number")

        if df.empty:
            return []

        model = IsolationForest()
        scores = model.fit_predict(df)

        anomaly_ratio = (scores == -1).mean()

        return [
            MLEvidence(
                model_name=self.name,
                signal_type="anomaly_score",
                score=anomaly_ratio,
                confidence=0.8,
                metadata={"samples": len(df)},
            )
        ]
