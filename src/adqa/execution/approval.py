from typing import Any

from .models import ActionPlan


class ApprovalManager:
    """
    Human-in-the-loop interface
    """

    def request(self, plan: ActionPlan) -> dict[str, Any]:
        return {
            "status": "PENDING_APPROVAL",
            "summary": plan.summary,
            "actions": [
                {"type": a.action_type, "reason": a.reason} for a in plan.actions
            ],
        }
