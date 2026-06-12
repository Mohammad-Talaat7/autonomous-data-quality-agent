# adqa/execution/self_healing.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import Action, ActionPlan

if TYPE_CHECKING:
    from ..explanation.remediation import RemediationProposal
    from ..scoring.models import QualityDecision


class SelfHealingController:
    """Auto-approve low-risk remediations when conditions are satisfied."""

    LOW_RISK_DECISIONS = frozenset({"PASS", "WARN"})
    LOW_RISK_SEVERITY = frozenset({"LOW", "MEDIUM"})
    AUTO_HEAL_ACTIONS = frozenset({
        "impute",
        "clip",
        "log_transform",
        "group_rare",
        "cast_type",
        "flag_nulls",
        "remove_anomalies",
        "remove_duplicates",
    })

    @staticmethod
    def can_auto_heal(decision: QualityDecision) -> bool:
        return (
            decision.decision in SelfHealingController.LOW_RISK_DECISIONS
            and decision.severity_level in SelfHealingController.LOW_RISK_SEVERITY
        )

    @staticmethod
    def auto_approve_low_risk(plan: ActionPlan, decision: QualityDecision) -> ActionPlan:
        if not SelfHealingController.can_auto_heal(decision):
            return plan

        auto_approved = False
        for action in plan.actions:
            op = (action.metadata or {}).get("operation", "")
            if op in SelfHealingController.AUTO_HEAL_ACTIONS:
                action.requires_approval = False
                auto_approved = True

        if auto_approved:
            plan.requires_human = any(a.requires_approval for a in plan.actions)
            plan.approved = plan.requires_human is False

        return plan

    @staticmethod
    def build_healing_proposal(
        proposal: RemediationProposal,
        decision: QualityDecision,
    ) -> Action | None:
        if not SelfHealingController.can_auto_heal(decision):
            return None
        if proposal.operational_mapping is None:
            return None
        if proposal.operational_mapping not in SelfHealingController.AUTO_HEAL_ACTIONS:
            return None

        return Action(
            action_type="REMEDIATE",
            reason=proposal.plain_language,
            requires_approval=False,
            metadata={
                "operation": proposal.operational_mapping,
                "column": proposal.column,
                "risk_level": proposal.risk_level,
                "auto_heal": True,
            },
        )
