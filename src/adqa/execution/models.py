from dataclasses import dataclass, field
from typing import Any


class ExecutionMode:
    ADVISORY: str = "advisory"
    HUMAN_IN_LOOP: str = "human"
    AUTOMATIC: str = "automatic"


@dataclass
class Action:
    action_type: str  # BLOCK / ALLOW / WARN / REQUEST_APPROVAL / LOG
    reason: str

    requires_approval: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionPlan:
    actions: list[Action]

    requires_human: bool

    summary: str

    approved: bool = False


@dataclass
class ExecutionResult:
    executed_actions: list[Action]

    approval_requested: bool

    blocked: bool

    advisory: str

    approval_payload: dict[str, Any] | None = None

    plan: ActionPlan | None = None
