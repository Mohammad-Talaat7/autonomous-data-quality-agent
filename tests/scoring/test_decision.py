from adqa.scoring.decision import DecisionEngine
from adqa.scoring.models import AggregatedScore


def test_decision_engine_boundaries():
    engine = DecisionEngine()

    # Test PASS
    agg_pass = AggregatedScore(
        global_score=0.1,
        issue_breakdown={},
        column_breakdown={},
        dimension_breakdown={},
        raw_scores=[],
    )
    decision = engine.decide(agg_pass)
    assert decision.decision == "PASS"
    assert decision.severity_level == "LOW"

    # Test WARN
    agg_warn = AggregatedScore(
        global_score=0.3,
        issue_breakdown={},
        column_breakdown={},
        dimension_breakdown={},
        raw_scores=[],
    )
    decision = engine.decide(agg_warn)
    assert decision.decision == "WARN"
    assert decision.severity_level == "MEDIUM"

    # Test FAIL
    agg_fail = AggregatedScore(
        global_score=0.6,
        issue_breakdown={},
        column_breakdown={},
        dimension_breakdown={},
        raw_scores=[],
    )
    decision = engine.decide(agg_fail)
    assert decision.decision == "FAIL"
    assert decision.severity_level == "HIGH"

    # Test CRITICAL
    agg_critical = AggregatedScore(
        global_score=0.8,
        issue_breakdown={},
        column_breakdown={},
        dimension_breakdown={},
        raw_scores=[],
    )
    decision = engine.decide(agg_critical)
    assert decision.decision == "FAIL"
    assert decision.severity_level == "CRITICAL"


def test_decision_explanation():
    engine = DecisionEngine()
    agg = AggregatedScore(
        global_score=0.5,
        issue_breakdown={"missing": 0.5, "validity": 0.3},
        column_breakdown={"col1": 0.5, "col2": 0.3},
        dimension_breakdown={"completeness": 0.5, "validity": 0.3},
        raw_scores=[],
    )

    decision = engine.decide(agg)

    assert "FAIL" in decision.explanation
    assert "0.500" in decision.explanation
    assert "missing" in decision.explanation
    assert "completeness" in decision.explanation
    assert "col1" in decision.explanation


def test_compute_severity_logic():
    engine = DecisionEngine()

    assert engine._compute_severity(0.0) == "LOW"
    assert engine._compute_severity(0.2) == "MEDIUM"
    assert engine._compute_severity(0.4) == "HIGH"
    assert engine._compute_severity(0.7) == "CRITICAL"
    assert engine._compute_severity(1.0) == "CRITICAL"
