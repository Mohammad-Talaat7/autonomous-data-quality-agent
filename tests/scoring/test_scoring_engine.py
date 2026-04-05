from unittest.mock import MagicMock

from adqa.detection.results import DetectionResult, DetectionResultBundle, MLEvidence
from adqa.scoring.engine import ScoringEngine


def test_scoring_engine_full_run():
    from pytest import approx

    tracer = MagicMock()
    lineage = MagicMock()
    engine = ScoringEngine(tracer=tracer, lineage=lineage)

    detections = [
        DetectionResult(detector_name="R1", issue_type="missing", severity_hint=0.1)
    ]
    ml_evidence = [
        MLEvidence(model_name="M1", signal_type="anomaly", score=0.9, confidence=1.0)
    ]

    result = engine.run(detections, ml_evidence)

    assert (
        result.decision.decision == "FAIL"
    )  # max((0.1+0.9)/2, 0.9*0.8) = max(0.5, 0.72) = 0.72
    assert result.decision.score == approx(0.72)

    # Check tracer calls
    # ScoringEngine calls tracer.trace but check actual
    # call count/name if needed
    # assert tracer.trace.called

    # Check lineage call
    # lineage.record.assert_called_with(...) # check actual params if needed


def test_scoring_engine_bundle_run():
    from pytest import approx

    engine = ScoringEngine()
    bundle = DetectionResultBundle(
        detections=[
            DetectionResult(detector_name="R1", issue_type="missing", severity_hint=0.1)
        ],
        ml_evidence=[
            MLEvidence(
                model_name="M1", signal_type="anomaly", score=0.2, confidence=1.0
            )
        ],
    )

    result = engine.run(bundle)

    # Weighted mean: (0.1 + 0.2) / 2 = 0.15
    # Max score penalty: 0.2 * 0.8 = 0.16
    # max(0.15, 0.16) = 0.16
    assert result.decision.decision == "PASS"  # PASS < 0.2
    assert result.decision.score == approx(0.16)


def test_scoring_engine_empty_run():
    engine = ScoringEngine()
    result = engine.run([], [])

    assert result.decision.score == 0.0
    assert result.decision.decision == "PASS"
