from adqa.scoring.aggregation.aggregator import Aggregator
from adqa.scoring.models import Score


def test_aggregator_empty_scores():
    aggregator = Aggregator()
    agg = aggregator.aggregate([])

    assert agg.global_score == 0.0
    assert agg.issue_breakdown == {}
    assert agg.column_breakdown == {}
    assert agg.dimension_breakdown == {}
    assert agg.raw_scores == []


def test_aggregator_single_critical_issue():
    # Test "Worst Case" penalty: 1 critical issue (severity 1.0)
    # Even if we have many passing ones, the global score should be at least 0.8
    aggregator = Aggregator()
    scores = [
        Score(
            detector_id="D1",
            rule_id="R1",
            issue_type="missing",
            dimension="completeness",
            column="col1",
            severity=1.0,
            confidence=1.0,
            weight=1.0,
            final_score=1.0,
        ),
        Score(
            detector_id="D2",
            rule_id="R2",
            issue_type="validity",
            dimension="validity",
            column="col2",
            severity=0.0,
            confidence=1.0,
            weight=1.0,
            final_score=0.0,
        ),
    ]

    agg = aggregator.aggregate(scores)

    # Weighted mean: (1.0 + 0.0) / (1.0 + 1.0) = 0.5
    # Max score penalty: 1.0 * 0.8 = 0.8
    # max(0.5, 0.8) = 0.8
    assert agg.global_score == 0.8
    assert agg.dimension_breakdown["completeness"] == 1.0
    assert agg.dimension_breakdown["validity"] == 0.0


def test_aggregator_many_minor_issues():
    # Test weighted mean dominance
    aggregator = Aggregator()
    scores = [
        Score(
            detector_id="D1",
            rule_id="R1",
            issue_type="minor1",
            dimension="dim1",
            column="col1",
            severity=0.1,
            confidence=1.0,
            weight=1.0,
            final_score=0.1,
        ),
        Score(
            detector_id="D2",
            rule_id="R2",
            issue_type="minor2",
            dimension="dim1",
            column="col1",
            severity=0.2,
            confidence=1.0,
            weight=1.0,
            final_score=0.2,
        ),
    ]

    agg = aggregator.aggregate(scores)

    # Weighted mean: (0.1 + 0.2) / 2 = 0.15
    # Max score penalty: 0.2 * 0.8 = 0.16
    # max(0.15, 0.16) = 0.16
    assert round(agg.global_score, 2) == 0.16


def test_aggregator_breakdowns():
    aggregator = Aggregator()
    scores = [
        Score(
            detector_id="D1",
            rule_id="R1",
            issue_type="type_A",
            dimension="completeness",
            column="col1",
            severity=0.4,
            confidence=1.0,
            weight=1.0,
            final_score=0.4,
        ),
        Score(
            detector_id="D2",
            rule_id="R2",
            issue_type="type_A",
            dimension="completeness",
            column="col2",
            severity=0.6,
            confidence=1.0,
            weight=1.0,
            final_score=0.6,
        ),
        Score(
            detector_id="D3",
            rule_id="R3",
            issue_type="type_B",
            dimension="validity",
            column="col1",
            severity=0.8,
            confidence=1.0,
            weight=1.0,
            final_score=0.8,
        ),
    ]

    agg = aggregator.aggregate(scores)

    from pytest import approx

    # Issue breakdown: type_A = (0.4 + 0.6) / 2 = 0.5, type_B = 0.8
    assert agg.issue_breakdown["type_A"] == approx(0.5)
    assert agg.issue_breakdown["type_B"] == approx(0.8)

    # Column breakdown: col1 = (0.4 + 0.8) / 2 = 0.6, col2 = 0.6
    assert agg.column_breakdown["col1"] == approx(0.6)
    assert agg.column_breakdown["col2"] == approx(0.6)

    # Dimension breakdown: completeness = (0.4 + 0.6) / 2 = 0.5, validity = 0.8
    assert agg.dimension_breakdown["completeness"] == approx(0.5)
    assert agg.dimension_breakdown["validity"] == approx(0.8)
