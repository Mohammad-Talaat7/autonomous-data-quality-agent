# adqa/explanation/root_cause.py
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from ..detection.results import DetectionResult, DetectionResultBundle
from ..profiling.models.dataset_profile import DatasetProfile
from ..scoring.models import AggregatedScore


@dataclass
class RootCauseHypothesis:
    cause: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    affected_columns: list[str] = field(default_factory=list)
    detector_ids: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)


class RootCauseEngine:
    def analyse(
        self,
        *,
        detections: DetectionResultBundle,
        scores: AggregatedScore,
        dataset_profile: DatasetProfile,
    ) -> Iterator[RootCauseHypothesis]:
        detection_by_type = self._index_by_type(detections)
        yield from self._missing_values_cause(detection_by_type)
        yield from self._correlation_cause(detection_by_type, dataset_profile)
        yield from self._duplicate_cause(detection_by_type, dataset_profile)
        yield from self._outlier_cause(detection_by_type)
        yield from self._pii_cause(detections)
        yield from self._anomaly_cause(detections)

    def _missing_values_cause(
        self, by_type: dict[str, list[DetectionResult]]
    ) -> Iterator[RootCauseHypothesis]:
        dets = by_type.get("missing_values", [])
        if not dets:
            return
        evidence: list[str] = []
        cols: list[str] = []
        ids: list[str] = []
        for d in dets:
            cols.append(d.column or "?")
            ids.append(d.id)
            if "observed_value" in d.metrics:
                evidence.append(
                    f"{d.column}: {float(d.metrics['observed_value']):.1%} missing"
                )
        yield RootCauseHypothesis(
            cause="missing_values",
            confidence=min(1.0, len(dets) * 0.12),
            evidence=evidence,
            affected_columns=cols,
            detector_ids=ids,
            caveats=["Check data pipeline ETL logic or source completeness."],
        )

    def _correlation_cause(
        self, by_type: dict[str, list[DetectionResult]], dataset_profile: DatasetProfile
    ) -> Iterator[RootCauseHypothesis]:
        dets = by_type.get("high_correlation", [])
        if not dets:
            return
        evidence: list[str] = []
        cols: list[str] = []
        ids: list[str] = []
        for d in dets:
            pair = d.columns or []
            cols.extend(pair)
            ids.append(d.id)
            if "observed_value" in d.metrics:
                evidence.append(
                    f"{pair}: correlation={float(d.metrics['observed_value']):.3f}"
                )
        yield RootCauseHypothesis(
            cause="high_correlation",
            confidence=min(1.0, len(dets) * 0.10),
            evidence=evidence,
            affected_columns=cols,
            detector_ids=ids,
            caveats=["Correlation may be spurious; check domain logic."],
        )

    def _duplicate_cause(
        self,
        by_type: dict[str, list[DetectionResult]],
        dataset_profile: DatasetProfile,
    ) -> Iterator[RootCauseHypothesis]:
        dets = by_type.get("duplicate_rows", [])
        if not dets:
            return
        evidence: list[str] = []
        ids: list[str] = []
        for d in dets:
            ids.append(d.id)
            if "observed_value" in d.metrics:
                evidence.append(
                    f"dataset duplicate ratio: {float(d.metrics['observed_value']):.1%}"
                )
        yield RootCauseHypothesis(
            cause="duplicate_rows",
            confidence=min(1.0, len(dets) * 0.10),
            evidence=evidence,
            detector_ids=ids,
            caveats=["Review upstream deduplication logic or join conditions."],
        )

    def _outlier_cause(
        self, by_type: dict[str, list[DetectionResult]]
    ) -> Iterator[RootCauseHypothesis]:
        dets = by_type.get("outliers", [])
        if not dets:
            return
        evidence: list[str] = []
        cols: list[str] = []
        ids: list[str] = []
        for d in dets:
            cols.append(d.column or "?")
            ids.append(d.id)
            if "observed_value" in d.metrics:
                evidence.append(
                    f"{d.column}: {float(d.metrics['observed_value']):.1%} outliers"
                )
        yield RootCauseHypothesis(
            cause="outliers",
            confidence=min(1.0, len(dets) * 0.10),
            evidence=evidence,
            affected_columns=cols,
            detector_ids=ids,
            caveats=["Outliers may be valid extreme values; review before treatment."],
        )

    def _pii_cause(
        self, bundle: DetectionResultBundle
    ) -> Iterator[RootCauseHypothesis]:
        dets = [
            e
            for e in bundle.ml_evidence
            if getattr(e, "signal_type", "") == "pii_detected"
        ]
        if not dets:
            return
        evidence: list[str] = []
        cols: list[str] = []
        ids: list[str] = []
        for e in dets:
            cols.append(getattr(e, "column", "?") or "?")
            ids.append(getattr(e, "id", "?"))
            pii_type = (e.metadata or {}).get("pii_type", "unknown")
            evidence.append(f"{getattr(e, 'column', '?')}: likely {pii_type}")
        yield RootCauseHypothesis(
            cause="pii_detected",
            confidence=min(1.0, len(dets) * 0.15),
            evidence=evidence,
            affected_columns=cols,
            detector_ids=ids,
            caveats=["Sensitive data should be masked or removed."],
        )

    def _anomaly_cause(
        self, bundle: DetectionResultBundle
    ) -> Iterator[RootCauseHypothesis]:
        dets = [
            e
            for e in bundle.ml_evidence
            if getattr(e, "signal_type", "") == "anomaly_score"
        ]
        if not dets:
            return
        evidence: list[str] = []
        ids: list[str] = []
        for e in dets:
            ids.append(getattr(e, "id", "?"))
            score = getattr(e, "score", 0.0)
            evidence.append(f"dataset anomaly ratio: {score:.1%}")
        yield RootCauseHypothesis(
            cause="anomaly_score",
            confidence=min(1.0, len(dets) * 0.08),
            evidence=evidence,
            detector_ids=ids,
            caveats=[
                "Isolation Forest anomalies may indicate data drift or corruption."
            ],
        )

    @staticmethod
    def _index_by_type(
        bundle: DetectionResultBundle,
    ) -> dict[str, list[DetectionResult]]:
        index: dict[str, list[DetectionResult]] = {}
        for d in bundle.detections:
            index.setdefault(d.issue_type or "unknown", []).append(d)
        return index
