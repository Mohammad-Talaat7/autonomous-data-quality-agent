from dataclasses import dataclass, field
from typing import Any


class ExecutionMode:
    ADVISORY: str = "advisory"
    HUMAN_IN_LOOP: str = "human"
    AUTOMATIC: str = "automatic"


@dataclass
class Action:
    action_type: str  # BLOCK / ALLOW / WARN / REQUEST_APPROVAL / LOG / REMEDIATE
    reason: str

    requires_approval: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "reason": self.reason,
            "requires_approval": self.requires_approval,
            "metadata": self.metadata,
        }


@dataclass
class ActionPlan:
    actions: list[Action]

    requires_human: bool

    summary: str

    approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "actions": [a.to_dict() for a in self.actions],
            "requires_human": self.requires_human,
            "summary": self.summary,
            "approved": self.approved,
        }


@dataclass
class ExecutionResult:
    executed_actions: list[Action]

    approval_requested: bool

    blocked: bool

    advisory: str

    approval_payload: dict[str, Any] | None = None

    plan: ActionPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "executed_actions": [a.to_dict() for a in self.executed_actions],
            "approval_requested": self.approval_requested,
            "blocked": self.blocked,
            "advisory": self.advisory,
            "approval_payload": self.approval_payload,
            "plan": self.plan.to_dict() if self.plan else None,
        }
