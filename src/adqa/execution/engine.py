from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

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

    def run(
        self,
        decision: QualityDecision,
        config: ADQAConfig,
        df: pd.DataFrame | None = None,
    ) -> tuple[ExecutionResult, pd.DataFrame | None]:
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
                trace_id = getattr(
                    getattr(self.tracer, "context", None), "trace_id", None
                )
                if trace_id:
                    self.lineage.record(
                        trace_id=trace_id,
                        operation="action_pending_approval",
                        inputs=decision,
                        outputs=approval_payload,
                    )

            result = ExecutionResult(
                executed_actions=[],
                approval_requested=True,
                blocked=False,
                advisory="Execution pending human approval",
                approval_payload=approval_payload,
                plan=plan,
            )
            return result, df

        # -------- execute actions --------
        return self.execute_plan(plan, df)

    def execute_plan(
        self, plan: ActionPlan, df: pd.DataFrame | None = None
    ) -> tuple[ExecutionResult, pd.DataFrame | None]:
        """
        Directly execute an ActionPlan (e.g. after approval)
        """
        result, processed_df = self.executor.execute(plan, tracer=self.tracer, df=df)
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
            trace_id = getattr(getattr(self.tracer, "context", None), "trace_id", None)
            if trace_id:
                self.lineage.record(
                    trace_id=trace_id,
                    operation="action_execution",
                    inputs=plan.summary,
                    outputs=result,
                )

        return result, processed_df
