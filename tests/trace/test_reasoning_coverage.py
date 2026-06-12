# tests/trace/test_reasoning_coverage.py

from adqa.detection.results import DetectionResult, DetectionResultBundle, MLEvidence
from adqa.trace.reasoning import collect_reason_codes


def test_collect_reason_codes_covers_common_issue_types():
    bundle = DetectionResultBundle(
        detections=[
            DetectionResult(detector_name="x", issue_type="missing_values"),
            DetectionResult(detector_name="x", issue_type="duplicate_rows"),
            DetectionResult(detector_name="x", issue_type="constant_column"),
            DetectionResult(detector_name="x", issue_type="outliers"),
            DetectionResult(detector_name="x", issue_type="high_skewness"),
            DetectionResult(detector_name="x", issue_type="high_correlation"),
            DetectionResult(detector_name="x", issue_type="range_violation"),
            DetectionResult(detector_name="x", issue_type="pattern_violation"),
        ],
        ml_evidence=[
            MLEvidence(model_name="x", signal_type="pii_detected"),
            MLEvidence(model_name="x", signal_type="anomaly_score"),
        ],
    )

    assert collect_reason_codes(bundle) == [
        "missing_values",
        "duplicate_rows",
        "constant_column",
        "outliers",
        "high_skewness",
        "high_correlation",
        "range_violation",
        "pattern_violation",
        "pii_detected",
        "anomaly_score",
    ]
