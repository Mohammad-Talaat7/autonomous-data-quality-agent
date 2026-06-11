"""Tests for SelfHealingController."""

from adqa.execution.models import Action, ActionPlan
from adqa.execution.self_healing import SelfHealingController
from adqa.scoring.models import QualityDecision


def _make_decision(decision: str, severity: str) -> QualityDecision:
    return QualityDecision(
        decision=decision,
        score=0.3,
        severity_level=severity,
        breakdown={},
        dimension_breakdown={},
        column_breakdown={},
        issue_map={},
        dominant_issues=[],
        affected_columns=[],
        thresholds_used={},
        explanation="test",
    )


def test_low_risk_warn_medium_can_auto_heal():
    decision = _make_decision("WARN", "MEDIUM")
    assert SelfHealingController.can_auto_heal(decision) is True


def test_fail_cannot_auto_heal():
    decision = _make_decision("FAIL", "LOW")
    assert SelfHealingController.can_auto_heal(decision) is False


def test_high_severity_cannot_auto_heal():
    decision = _make_decision("WARN", "HIGH")
    assert SelfHealingController.can_auto_heal(decision) is False


def test_auto_approve_reduces_approval_requirements():
    decision = _make_decision("WARN", "MEDIUM")
    plan = ActionPlan(
        actions=[
            Action(
                action_type="REMEDIATE",
                reason="impute missing",
                requires_approval=True,
                metadata={"operation": "impute", "column": "email"},
            ),
            Action(
                action_type="REMEDIATE",
                reason="mask pii",
                requires_approval=True,
                metadata={"operation": "mask_pii", "column": "ssn"},
            ),
        ],
        requires_human=True,
        summary="test",
    )

    result = SelfHealingController.auto_approve_low_risk(plan, decision)

    # impute should be auto-approved, mask_pii still needs approval
    assert result.actions[0].requires_approval is False  # impute auto-approved
    assert result.actions[1].requires_approval is True   # mask_pii stays
    assert result.requires_human is True  # still needs human for mask_pii
    assert result.approved is False


def test_auto_approve_all_low_risk():
    decision = _make_decision("PASS", "LOW")
    plan = ActionPlan(
        actions=[
            Action(
                action_type="REMEDIATE",
                reason="clip outliers",
                requires_approval=True,
                metadata={"operation": "clip", "column": "score"},
            ),
        ],
        requires_human=True,
        summary="test",
    )

    result = SelfHealingController.auto_approve_low_risk(plan, decision)
    assert result.actions[0].requires_approval is False
    assert result.requires_human is False
    assert result.approved is True
