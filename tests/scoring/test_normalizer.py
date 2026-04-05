from adqa.detection.results import DetectionResult, MLEvidence
from adqa.scoring.normalizer import normalize_detection_results


def test_normalize_rule_result():
    res = DetectionResult(
        detector_name="DetectorA",
        issue_type="missing_values",
        dimension="completeness",
        column="col1",
        severity_hint=0.5,
        confidence=0.9,
        metrics={"count": 10},
    )

    normalized = normalize_detection_results([res])

    assert len(normalized) == 1
    n = normalized[0]
    assert n.detector_id == "DetectorA"
    assert n.rule_id == "missing_values"
    assert n.issue_type == "missing_values"
    assert n.dimension == "completeness"
    assert n.column == "col1"
    assert n.severity == 0.5
    assert n.confidence == 0.9
    assert n.metadata == {"count": 10}


def test_normalize_ml_evidence():
    ev = MLEvidence(
        model_name="ModelX",
        signal_type="outlier",
        dimension="validity",
        column="col2",
        score=0.7,
        confidence=0.8,
        metadata={"p_value": 0.01},
    )

    normalized = normalize_detection_results([], ml_evidence=[ev])

    assert len(normalized) == 1
    n = normalized[0]
    assert n.detector_id == "ModelX"
    assert n.rule_id == "outlier"
    assert n.issue_type == "outlier"
    assert n.dimension == "validity"
    assert n.column == "col2"
    assert n.severity == 0.7
    assert n.confidence == 0.8
    assert n.metadata == {"p_value": 0.01}


def test_normalize_mixed_results():
    res = DetectionResult(detector_name="R1", issue_type="missing", severity_hint=0.1)
    ev = MLEvidence(model_name="M1", signal_type="anomaly", score=0.9)

    normalized = normalize_detection_results([res], [ev])

    assert len(normalized) == 2
    assert normalized[0].detector_id == "R1"
    assert normalized[1].detector_id == "M1"


def test_normalize_empty():
    assert normalize_detection_results([], []) == []
    assert normalize_detection_results(None, None) == []
