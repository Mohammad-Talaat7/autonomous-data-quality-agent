from __future__ import annotations

from ..models.column_profile import ColumnProfile
from ..models.correlation_profile import CorrelationProfile
from ..models.dataset_profile import DatasetMetadata
from ..models.risk_signal import RiskSignal, RiskSignalType


def build_risk_signals(
    metadata: DatasetMetadata,
    columns: tuple[ColumnProfile, ...],
    correlations: CorrelationProfile | None,
) -> tuple[RiskSignal, ...]:

    signals: list[RiskSignal] = []

    # =========================
    # Dataset-Level Signals
    # =========================

    signals.append(
        RiskSignal(
            type=RiskSignalType.NULL_RATIO,
            subject="dataset",
            value=metadata.total_null_ratio,
        )
    )

    signals.append(
        RiskSignal(
            type=RiskSignalType.DUPLICATE_RATIO,
            subject="dataset",
            value=metadata.duplicate_row_ratio,
        )
    )

    # =========================
    # Column-Level Signals
    # =========================

    for column in columns:
        name = column.name
        sm = column.structural_metrics

        # Raw structural signals
        signals.append(
            RiskSignal(
                type=RiskSignalType.NULL_RATIO,
                subject=name,
                value=sm.null_ratio,
            )
        )

        signals.append(
            RiskSignal(
                type=RiskSignalType.UNIQUE_RATIO,
                subject=name,
                value=sm.unique_ratio,
            )
        )

        signals.append(
            RiskSignal(
                type=RiskSignalType.DUPLICATE_RATIO,
                subject=name,
                value=sm.duplicate_ratio,
            )
        )

        if sm.unique_ratio == 1.0:
            signals.append(
                RiskSignal(
                    type=RiskSignalType.IDENTIFIER_LIKELIHOOD,
                    subject=name,
                    value=True,
                    metadata={"reason": "unique_ratio_equals_1"},
                )
            )

        if column.behavioral_metrics:
            bm = column.behavioral_metrics

            signals.append(
                RiskSignal(
                    type=RiskSignalType.OUTLIER_RATIO,
                    subject=name,
                    value=bm.outlier_ratio,
                )
            )

            signals.append(
                RiskSignal(
                    type=RiskSignalType.HEAVY_TAIL,
                    subject=name,
                    value=bm.heavy_tail_score,
                )
            )

            signals.append(
                RiskSignal(
                    type=RiskSignalType.MULTIMODALITY,
                    subject=name,
                    value=bm.multimodality_score,
                )
            )

            signals.append(
                RiskSignal(
                    type=RiskSignalType.LOW_VARIANCE,
                    subject=name,
                    value=bm.low_variance_indicator,
                )
            )

    # =========================
    # Correlation Signals
    # =========================

    if correlations:
        signals.append(
            RiskSignal(
                type=RiskSignalType.CORRELATION_DENSITY,
                subject="dataset",
                value=correlations.correlation_density_score,
            )
        )

        for (col1, col2), value in correlations.matrix.items():
            if col1 == col2:
                continue

            signals.append(
                RiskSignal(
                    type=RiskSignalType.CORRELATION,
                    subject=f"{col1}__{col2}",
                    value=value,
                    metadata={"col1": col1, "col2": col2},
                )
            )

    return tuple(signals)
