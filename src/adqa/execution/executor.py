from collections.abc import Callable
from typing import Any

from .models import Action, ActionPlan, ExecutionResult

ActionHandler = Callable[[Action, Any], None]  # (Action, Tracer) -> None


class ActionExecutor:
    """
    Safe executor with extensible handlers for side effects
    """

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register_handler(self, action_type: str, handler: ActionHandler) -> None:
        """
        Register a custom side-effect handler for an action type
        """
        self._handlers[action_type] = handler

    def execute(self, plan: ActionPlan, tracer: Any = None) -> ExecutionResult:
        executed = []
        approval_requested = False
        blocked = False

        for action in plan.actions:
            if tracer:
                tracer.trace(
                    "ACTION_START",
                    {
                        "action_type": action.action_type,
                        "reason": action.reason,
                        "requires_approval": action.requires_approval,
                    },
                )

            # -------- 1. Check Approval --------
            # If not approved, skip any action requiring it
            if action.requires_approval and not plan.approved:
                approval_requested = True

                if tracer:
                    tracer.trace(
                        "ACTION_SKIPPED_PENDING_APPROVAL",
                        {"action_type": action.action_type},
                    )

                continue

            # -------- 2. Run Side Effect Handlers --------
            handler = self._handlers.get(action.action_type)
            if handler:
                try:
                    handler(action, tracer)
                except Exception as e:
                    if tracer:
                        tracer.trace(
                            "ACTION_HANDLER_ERROR",
                            {"error": str(e), "type": action.action_type},
                        )

            # -------- 3. Record Execution --------
            executed.append(action)

            if tracer:
                tracer.trace("ACTION_EXECUTED", {"action_type": action.action_type})

            # -------- 4. STOP ON BLOCK --------
            if action.action_type == "BLOCK":
                blocked = True

                if tracer:
                    tracer.trace("ACTION_EXECUTION_BLOCKED", {"reason": action.reason})

                break

        advisory = self._build_advisory(plan)

        return ExecutionResult(
            executed_actions=executed,
            approval_requested=approval_requested,
            blocked=blocked,
            advisory=advisory,
        )

    def _build_advisory(self, plan: ActionPlan) -> str:
        return " | ".join(f"[{a.action_type}] {a.reason}" for a in plan.actions)
