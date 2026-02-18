from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..models.column_profile import ColumnProfile
from ..models.ml_profile import MLProfile
from .anomaly_amplifier import amplify_numeric_anomalies
from .semantic_classifier import classify_column_semantic


def run_ml_profiling(
    df: pd.DataFrame,
    column_profiles: tuple[ColumnProfile, ...],
    random_state: int = 42,
    thresholds: ProfilingThresholds | None = None,
) -> tuple[MLProfile, ...]:

    ml_results = []

    for profile in column_profiles:
        series = df[profile.name]

        semantic_profile = classify_column_semantic(
            series, profile, thresholds=thresholds
        )
        if semantic_profile:
            ml_results.append(semantic_profile)

        anomaly_profile = amplify_numeric_anomalies(
            series,
            profile,
            random_state=random_state,
            thresholds=thresholds,
        )
        if anomaly_profile:
            ml_results.append(anomaly_profile)

    return tuple(ml_results)
