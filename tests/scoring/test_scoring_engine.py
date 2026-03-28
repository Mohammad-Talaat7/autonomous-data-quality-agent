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

    decision = engine.run(detections, ml_evidence)

    assert (
        decision.decision == "FAIL"
    )  # max((0.1+0.9)/2, 0.9*0.8) = max(0.5, 0.72) = 0.72
    assert decision.score == approx(0.72)

    # Check tracer calls
    assert tracer.trace.called
    # COMPUTE_SCORE, AGGREGATE_SCORE, QUALITY_DECISION
    assert tracer.trace.call_count >= 3

    # Check lineage call
    lineage.record.assert_called_with(
        "quality_decision", inputs=detections + ml_evidence, outputs=decision
    )


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

    decision = engine.run(bundle)

    # Weighted mean: (0.1 + 0.2) / 2 = 0.15
    # Max score penalty: 0.2 * 0.8 = 0.16
    # max(0.15, 0.16) = 0.16
    assert decision.decision == "PASS"  # PASS < 0.2
    assert decision.score == approx(0.16)


def test_scoring_engine_empty_run():
    engine = ScoringEngine()
    decision = engine.run([], [])

    assert decision.score == 0.0
    assert decision.decision == "PASS"
