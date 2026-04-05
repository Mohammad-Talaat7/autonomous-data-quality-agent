from adqa.scoring.models import NormalizedDetection
from adqa.scoring.scorers.rule_scorer import RuleScorer


def test_rule_scorer_default_weight():
    scorer = RuleScorer()
    detection = NormalizedDetection(
        detector_id="D1",
        rule_id="missing_values",
        issue_type="missing_values",
        dimension="completeness",
        column="col1",
        severity=0.5,
        confidence=1.0,
    )

    score = scorer.compute(detection)

    assert score.weight == 1.0
    assert score.final_score == 0.5


def test_rule_scorer_custom_weight():
    weight_map = {"missing_values": 2.0}
    scorer = RuleScorer(weight_map=weight_map)
    detection = NormalizedDetection(
        detector_id="D1",
        rule_id="missing_values",
        issue_type="missing_values",
        dimension="completeness",
        column="col1",
        severity=0.5,
        confidence=1.0,
    )

    score = scorer.compute(detection)

    assert score.weight == 2.0
    assert score.final_score == 1.0


def test_rule_scorer_with_confidence():
    scorer = RuleScorer()
    detection = NormalizedDetection(
        detector_id="D1",
        rule_id="R1",
        issue_type="T1",
        dimension="dim1",
        column="col1",
        severity=0.8,
        confidence=0.5,
    )

    score = scorer.compute(detection)

    # 0.8 * 0.5 * 1.0 = 0.4
    assert score.final_score == 0.4
