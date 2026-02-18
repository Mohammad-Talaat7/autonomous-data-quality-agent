from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..models.column_profile import ColumnProfile, LogicalType
from ..models.ml_profile import MLProfile

MODEL_NAME = "anomaly_amplifier"
MODEL_VERSION = "1.0"


def amplify_numeric_anomalies(
    series: pd.Series[Any],
    column_profile: ColumnProfile,
    random_state: int = 42,
    thresholds: ProfilingThresholds | None = None,
) -> MLProfile | None:

    if column_profile.logical_type != LogicalType.NUMERIC:
        return None

    clean = series.dropna()

    min_rows = thresholds.min_rows_anomaly_detection if thresholds else 20
    contamination = thresholds.anomaly_contamination if thresholds else "auto"
    n_estimators = thresholds.anomaly_n_estimators if thresholds else 50
    seed = thresholds.global_seed if thresholds else random_state

    if len(clean) < min_rows:
        return None

    values = clean.to_numpy().reshape(-1, 1)

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=seed,
    )

    model.fit(values)

    scores = model.decision_function(values)
    predictions = model.predict(values)

    anomaly_ratio = float((predictions == -1).sum() / len(predictions))
    mean_score = float(np.mean(scores))

    return MLProfile(
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        target=column_profile.name,
        outputs={
            "anomaly_ratio": anomaly_ratio,
            "mean_anomaly_score": mean_score,
        },
    )
