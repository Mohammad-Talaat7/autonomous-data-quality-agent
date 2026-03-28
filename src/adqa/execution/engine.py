from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .approval import ApprovalManager
from .executor import ActionExecutor
from .models import ActionPlan, ExecutionResult
from .policy import ExecutionPolicy

if TYPE_CHECKING:
    from ..config.model import ADQAConfig
    from ..scoring.models import QualityDecision


class ExecutionEngine:
    def __init__(self, tracer: Any = None, lineage: Any = None) -> None:
        self.tracer = tracer
        self.lineage = lineage

        self.policy = ExecutionPolicy()
        self.executor = ActionExecutor()
        self.approval = ApprovalManager()

    def run(self, decision: QualityDecision, config: ADQAConfig) -> ExecutionResult:
        """
        Evaluate policy using config and execute safe actions, or request approval.
        """
        # -------- policy evaluation --------
        plan = self.policy.evaluate(decision, config)

        if self.tracer:
            self.tracer.trace(
                "ACTION_PLAN",
                {
                    "summary": plan.summary,
                    "num_actions": len(plan.actions),
                    "requires_human": plan.requires_human,
                },
            )

        # -------- approval required --------
        if plan.requires_human:
            approval_payload = self.approval.request(plan)

            if self.tracer:
                self.tracer.trace("ACTION_APPROVAL_REQUIRED", approval_payload)

            if self.lineage:
                self.lineage.record(
                    "action_pending_approval", inputs=decision, outputs=approval_payload
                )

            return ExecutionResult(
                executed_actions=[],
                approval_requested=True,
                blocked=False,
                advisory="Execution pending human approval",
                approval_payload=approval_payload,
                plan=plan,
            )

        # -------- execute actions --------
        return self.execute_plan(plan)

    def execute_plan(self, plan: ActionPlan) -> ExecutionResult:
        """
        Directly execute an ActionPlan (e.g. after approval)
        """
        result = self.executor.execute(plan, tracer=self.tracer)
        result.plan = plan  # Ensure plan is attached to the result

        if self.tracer:
            self.tracer.trace(
                "ACTION_RESULT",
                {
                    "executed_count": len(result.executed_actions),
                    "approval_requested": result.approval_requested,
                    "blocked": result.blocked,
                },
            )

        # -------- lineage --------
        if self.lineage:
            self.lineage.record("action_execution", inputs=plan.summary, outputs=result)

        return result
