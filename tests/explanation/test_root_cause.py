# tests/explanation/test_root_cause.py

"""Tests for RootCauseEngine."""

from unittest.mock import MagicMock

from adqa.detection.results import DetectionResult, DetectionResultBundle, MLEvidence
from adqa.explanation.root_cause import RootCauseEngine, RootCauseHypothesis
from adqa.profiling.models.dataset_profile import DatasetMetadata, DatasetProfile
from adqa.scoring.models import AggregatedScore


def _make_profile():
    metadata = DatasetMetadata(
        row_count=200,
        column_count=4,
        duplicate_row_ratio=0.05,
        memory_usage_bytes=8192,
        total_null_ratio=0.15,
        type_distribution={"int64": 2, "str": 2},
    )
    return DatasetProfile(metadata=metadata, columns=(), correlations=None)


def test_missing_values_cause():
    engine = RootCauseEngine()
    det = DetectionResult(
        detector_name="MissingValuesDetector",
        issue_type="missing_values",
        column="email",
        severity_hint=0.45,
        metrics={"observed_value": 0.45, "threshold": 0.2},
        description="email has 45% missing",
    )
    bundle = DetectionResultBundle(detections=[det], ml_evidence=[])
    scores = AggregatedScore(
        global_score=0.35,
        issue_breakdown={"missing_values": 0.45},
        column_breakdown={"email": 0.45},
        dimension_breakdown={"completeness": 0.45},
        raw_scores=[],
    )

    causes = list(engine.analyse(detections=bundle, scores=scores, dataset_profile=_make_profile()))

    missing = [c for c in causes if c.cause == "missing_values"]
    assert len(missing) == 1
    assert missing[0].evidence
    assert "45.0%" in missing[0].evidence[0]


def test_no_detections_returns_empty():
    engine = RootCauseEngine()
    bundle = DetectionResultBundle(detections=[], ml_evidence=[])
    scores = AggregatedScore(
        global_score=0.0,
        issue_breakdown={},
        column_breakdown={},
        dimension_breakdown={},
        raw_scores=[],
    )

    causes = list(engine.analyse(detections=bundle, scores=scores, dataset_profile=_make_profile()))

    assert len(causes) == 0


def test_pii_cause():
    engine = RootCauseEngine()
    ml = MLEvidence(
        model_name="PIIDetector",
        signal_type="pii_detected",
        column="ssn",
        score=0.92,
        confidence=0.9,
        metadata={"pii_type": "ssn", "pii_score": 0.92},
    )
    bundle = DetectionResultBundle(detections=[], ml_evidence=[ml])
    scores = AggregatedScore(
        global_score=0.8,
        issue_breakdown={"pii_detected": 0.8},
        column_breakdown={"ssn": 0.8},
        dimension_breakdown={"privacy": 0.8},
        raw_scores=[],
    )

    causes = list(engine.analyse(detections=bundle, scores=scores, dataset_profile=_make_profile()))

    pii = [c for c in causes if c.cause == "pii_detected"]
    assert len(pii) == 1
    assert "ssn" in pii[0].evidence[0]


def test_correlation_cause():
    engine = RootCauseEngine()
    det = DetectionResult(
        detector_name="CorrelationDetector",
        issue_type="high_correlation",
        columns=["col_a", "col_b"],
        scope="cross_column",
        severity_hint=0.95,
        metrics={"observed_value": 0.95, "threshold": 0.9},
        description="col_a and col_b highly correlated",
    )
    bundle = DetectionResultBundle(detections=[det], ml_evidence=[])
    scores = AggregatedScore(
        global_score=0.9,
        issue_breakdown={"high_correlation": 0.9},
        column_breakdown={"col_a": 0.9},
        dimension_breakdown={"consistency": 0.9},
        raw_scores=[],
    )

    causes = list(engine.analyse(detections=bundle, scores=scores, dataset_profile=_make_profile()))

    corr = [c for c in causes if c.cause == "high_correlation"]
    assert len(corr) == 1
    assert "0.950" in corr[0].evidence[0]
