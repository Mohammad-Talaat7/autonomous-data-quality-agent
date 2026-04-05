from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from adqa.detection.engine import DetectionEngine
from adqa.detection.ml_detectors.isolation_forest import IsolationForestDetector
from adqa.detection.ml_detectors.pii import PIIDetector
from adqa.detection.results import DetectionResult, MLEvidence
from adqa.detection.rule_detectors.missing import MissingValuesDetector


def test_detection_engine_run():
    # Setup mocks
    rule_detector = MagicMock(spec=MissingValuesDetector)
    rule_detector.detect.return_value = [
        DetectionResult(detector_name="MockRule", issue_type="test_issue")
    ]

    ml_detector = MagicMock(spec=IsolationForestDetector)
    ml_detector.run_model.return_value = [
        MLEvidence(model_name="MockML", signal_type="test_signal")
    ]

    engine = DetectionEngine(rule_detectors=[rule_detector], ml_detectors=[ml_detector])

    dataset_profile = MagicMock()
    column_profiles = {"col1": MagicMock()}
    ml_profiles = MagicMock()

    bundle = engine.run(
        dataset_profile=dataset_profile,
        column_profiles=column_profiles,
        ml_profiles=ml_profiles,
    )

    assert len(bundle.detections) == 1
    assert bundle.detections[0].detector_name == "MockRule"

    assert len(bundle.ml_evidence) == 1
    assert bundle.ml_evidence[0].model_name == "MockML"

    rule_detector.detect.assert_called_once()
    ml_detector.run_model.assert_called_once()


def test_detection_engine_tracing():
    tracing = MagicMock()
    # Mocking a context manager
    tracing.span.return_value.__enter__.return_value = None

    rule_detector = MagicMock(spec=MissingValuesDetector)
    rule_detector.detect.return_value = []

    engine = DetectionEngine(
        rule_detectors=[rule_detector], ml_detectors=[], tracing=tracing
    )

    engine.run(dataset_profile=MagicMock(), column_profiles={})

    tracing.span.assert_any_call(
        "RUN_DETECTOR", detector=rule_detector.__class__.__name__
    )


def test_detection_engine_correlation_extraction():
    detector = MagicMock(spec=MissingValuesDetector)
    detector.detect.return_value = []

    engine = DetectionEngine(rule_detectors=[detector], ml_detectors=[])

    # Mock dataset profile with correlations
    dataset_profile = MagicMock()
    correlations = MagicMock()
    correlations.matrix = {("A", "B"): 0.9}
    dataset_profile.correlations = correlations

    engine.run(dataset_profile=dataset_profile, column_profiles={})

    # Verify that the detector received the correlation matrix
    call_args = detector.detect.call_args[0][0]
    assert call_args.correlation_matrix is not None
    assert call_args.correlation_matrix == correlations.matrix


def test_isolation_forest_detector():
    # Real test with mocked IsolationForest class inside the detector module
    import numpy as np

    with patch(
        "adqa.detection.ml_detectors.isolation_forest.IsolationForest"
    ) as mock_if_class:
        mock_model = MagicMock()
        mock_model.fit_predict.return_value = np.array([-1, 1, 1, 1])  # 25% anomalies
        mock_if_class.return_value = mock_model

        thresholds = MagicMock()
        thresholds.min_rows_anomaly_detection = 0
        detector = IsolationForestDetector(thresholds=thresholds)
        context = MagicMock()
        context.raw_data_sample = pd.DataFrame({"A": [1, 2, 3, 4]})

        evidence = detector.run_model(context)

        assert len(evidence) == 1
        assert evidence[0].model_name == "IsolationForest"
        assert evidence[0].score == 0.25


def test_pii_detector():
    detector = PIIDetector()

    ml_profile = MagicMock()
    ml_profile.model_name = "semantic_classifier"
    ml_profile.target = "email_col"
    ml_profile.outputs = {"predicted_class": "email", "confidence": 0.95}

    context = MagicMock()
    context.ml_profiles = [ml_profile]

    results = detector.run_model(context)
    assert len(results) == 1
    assert results[0].signal_type == "pii_detected"
    assert results[0].metadata["pii_type"] == "email"
