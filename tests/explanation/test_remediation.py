# tests/explanation/test_remediation.py

"""Tests for RemediationProposalEngine."""

from adqa.explanation.remediation import (
    RemediationProposalEngine,
    RemediationProposalBundle,
)
from adqa.scoring.models import QualityDecision


def _make_decision(decision: str, severity: str, issue_map: dict):
    return QualityDecision(
        decision=decision,
        score=0.5,
        severity_level=severity,
        breakdown={},
        dimension_breakdown={},
        column_breakdown={},
        issue_map=issue_map,
        dominant_issues=list(issue_map.keys()),
        affected_columns=[],
        thresholds_used={},
        explanation="test",
    )


def test_missing_values_maps_to_impute():
    engine = RemediationProposalEngine()
    decision = _make_decision("WARN", "MEDIUM", {"missing_values": ["email"]})

    bundle = engine.propose(decision=decision, action_plan=None)

    missing = [p for p in bundle.proposals if p.issue_type == "missing_values"]
    assert len(missing) == 1
    assert missing[0].proposed_action == "impute"
    assert missing[0].operational_mapping == "impute"
    assert missing[0].risk_level == "medium"


def test_pii_maps_to_mask():
    engine = RemediationProposalEngine()
    decision = _make_decision("FAIL", "HIGH", {"pii_detected": ["ssn"]})

    bundle = engine.propose(decision=decision, action_plan=None)

    pii = [p for p in bundle.proposals if p.issue_type == "pii_detected"]
    assert len(pii) == 1
    assert pii[0].proposed_action == "mask_pii"
    assert pii[0].risk_level == "high"


def test_all_proposals_are_non_executable_by_default():
    engine = RemediationProposalEngine()
    decision = _make_decision(
        "WARN", "LOW", {"missing_values": ["a"], "duplicate_rows": []}
    )

    bundle = engine.propose(decision=decision, action_plan=None)

    for p in bundle.proposals:
        assert p.requires_approval is True
        assert p.unsupported_suggestions == []
        assert p.operational_mapping is not None
