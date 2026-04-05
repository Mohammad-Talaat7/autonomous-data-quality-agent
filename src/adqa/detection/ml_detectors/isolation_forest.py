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

    def __init__(self, thresholds: Any | None = None, **kwargs: Any) -> None:
        # thresholds here could be DetectionThresholds or ProfilingThresholds
        # We look for min_rows_anomaly_detection
        self.min_rows = getattr(thresholds, "min_rows_anomaly_detection", 20)

    def run_model(self, context: DetectionContext) -> list[MLEvidence]:
        if IsolationForest is None:
            # Skip if scikit-learn is not installed
            return []

        if (
            context.raw_data_sample is None
            or len(context.raw_data_sample) < self.min_rows
        ):
            return []

        df = context.raw_data_sample.select_dtypes(include="number")

        if df.empty:
            return []

        try:
            model = IsolationForest()
            preds = model.fit_predict(df)
        except Exception:
            return []

        # Get indices of anomalies
        # IsolationForest returns -1 for anomalies
        anomaly_mask = preds == -1
        anomaly_ratio = float(anomaly_mask.mean())

        # Get actual row indices from the original dataframe
        anomaly_indices = context.raw_data_sample.index[anomaly_mask].tolist()

        return [
            MLEvidence(
                model_name=self.name,
                signal_type="anomaly_score",
                score=anomaly_ratio,
                confidence=0.8,
                metadata={
                    "samples": len(df),
                    "indices": anomaly_indices,
                    "anomaly_count": len(anomaly_indices),
                },
            )
        ]
