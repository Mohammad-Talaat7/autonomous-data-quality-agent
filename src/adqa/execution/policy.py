from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Action, ActionPlan, ExecutionMode

if TYPE_CHECKING:
    from ..config.model import ADQAConfig
    from ..scoring.models import QualityDecision


class ExecutionPolicy:
    """
    Deterministic mapping from QualityDecision → ActionPlan based on ADQAConfig
    """

    def evaluate(self, decision: QualityDecision, config: ADQAConfig) -> ActionPlan:
        """
        Evaluate policy using ADQAConfig
        """
        mode = config.execution_mode
        actions: list[Action] = []

        # -------- 1. Base Decision Mapping --------
        if decision.severity_level == "CRITICAL" or decision.decision == "FAIL":
            actions.append(self._create_base_failure_action(decision, mode))
        elif decision.decision == "WARN":
            actions.append(
                Action(
                    action_type="WARN",
                    reason="Quality degradation detected",
                    metadata={"decision": "WARN"},
                )
            )
        else:
            actions.append(
                Action(
                    action_type="ALLOW",
                    reason="Data quality acceptable",
                    metadata={"decision": "PASS"},
                )
            )

        # -------- 2. Issue-based Actions --------
        actions.extend(self._issue_based_actions(decision, config))

        # -------- 3. Mode-specific adjustments --------
        # In ADVISORY mode, nothing should actually block or require approval
        if mode == ExecutionMode.ADVISORY:
            for action in actions:
                if action.action_type == "BLOCK":
                    action.action_type = "WARN"
                    action.reason = f"[ADVICE ONLY] Would have blocked: {action.reason}"
                action.requires_approval = False

        requires_human = any(a.requires_approval for a in actions)

        return ActionPlan(
            actions=actions,
            requires_human=requires_human,
            summary=self._build_summary(decision, actions),
        )

    def _create_base_failure_action(
        self, decision: QualityDecision, mode: str
    ) -> Action:
        meta = {"decision": decision.decision, "severity": decision.severity_level}

        if mode == ExecutionMode.AUTOMATIC:
            return Action(
                action_type="BLOCK",
                reason=f"Automatic block due to {decision.decision} quality",
                metadata=meta,
            )
        elif mode == ExecutionMode.HUMAN_IN_LOOP:
            return Action(
                action_type="BLOCK",
                reason=f"Quality {decision.decision} requires manual intervention",
                requires_approval=True,
                metadata=meta,
            )
        else:  # ADVISORY
            return Action(
                action_type="WARN",
                reason=f"Quality {decision.decision} detected (Advisory)",
                metadata=meta,
            )

    def _issue_based_actions(
        self, decision: QualityDecision, config: ADQAConfig
    ) -> list[Action]:
        actions = []
        mode = config.execution_mode

        # Schema issues -> usually a block
        if "schema_violation" in decision.dominant_issues:
            actions.append(
                Action(
                    action_type="BLOCK",
                    reason="Schema violation detected",
                    requires_approval=(mode == ExecutionMode.HUMAN_IN_LOOP),
                    metadata={"issue": "schema_violation"},
                )
            )

        # Missing values -> request approval in Human-in-loop, otherwise warn
        if "missing_values" in decision.dominant_issues:
            if mode == ExecutionMode.HUMAN_IN_LOOP:
                actions.append(
                    Action(
                        action_type="REQUEST_APPROVAL",
                        reason="Missing values detected",
                        requires_approval=True,
                        metadata={"issue": "missing_values"},
                    )
                )
            else:
                actions.append(
                    Action(
                        action_type="WARN",
                        reason="Missing values detected",
                        metadata={"issue": "missing_values"},
                    )
                )

        return actions

    def _build_summary(self, decision: QualityDecision, actions: list[Action]) -> str:
        action_types = [a.action_type for a in actions]
        return (
            f"{decision.decision} (score={decision.score:.3f}) → "
            f"{', '.join(action_types)}"
        )
