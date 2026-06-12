# adqa/explanation/remediation.py
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from ..execution.models import ActionPlan
from ..llm.client import BaseLLMClient
from ..llm.models import LLMRequest, RemediationProposalRequest
from ..llm.prompts import build_json_messages
from ..scoring.models import QualityDecision

ALLOWED_ACTIONS: dict[str, str] = {
    "drop_column": "drop_column",
    "remove_duplicates": "remove_duplicates",
    "impute": "impute",
    "clip": "clip",
    "log_transform": "log_transform",
    "group_rare": "group_rare",
    "cast_type": "cast_type",
    "mask_pii": "mask_pii",
    "remove_anomalies": "remove_anomalies",
    "flag_nulls": "flag_nulls",
}


@dataclass
class RemediationProposal:
    issue_type: str
    proposed_action: str | None
    operational_mapping: str | None
    column: str | None
    risk_level: Literal["low", "medium", "high"]
    requires_approval: bool
    plain_language: str
    unsupported_suggestions: list[str] = field(default_factory=list)


@dataclass
class RemediationProposalBundle:
    proposals: list[RemediationProposal] = field(default_factory=list)

PROMPT_VERSION = "adqa.remediation.v1"
REMEDIATION_SYSTEM = (
    "You are ADQA's remediation agent. "
    "Given a data quality issue and affected columns, propose concrete code-based fixes. "
    "Return strict JSON with keys: proposals (list of strings), risk_level (low/medium/high), "
    "requires_human_review (boolean)."
)

class RemediationAgent:
    """LLM-powered remediation proposal generator."""

    def __init__(self, *, client: BaseLLMClient, config: Any = None) -> None:
        self._client = client
        self._model = model
        self._config = config

    def propose(
        self,
        *,
        decision: QualityDecision,
        action_plan: ActionPlan | None = None,
    ) -> RemediationProposalBundle:
        proposals: list[RemediationProposal] = []

        # Get deterministic proposals first as fallback
        engine = RemediationProposalEngine()
        deterministic = engine.propose(decision=decision, action_plan=action_plan)
        det_map = {p.issue_type: p for p in deterministic.proposals}

        for issue_type, cols in decision.issue_map.items():
            try:
                llm_proposal = self._llm_propose(issue_type, cols, decision)
                proposal = RemediationProposal(
                    issue_type=issue_type,
                    proposed_action=llm_proposal.get("action"),
                    operational_mapping=None,
                    column=cols[0] if cols else None,
                    risk_level=llm_proposal.get("risk_level", "low"),
                    requires_approval=True,
                    plain_language=llm_proposal.get("description", ""),
                )

                # Validate against allowed actions
                action = proposal.proposed_action
                if action and action in ALLOWED_ACTIONS:
                    proposal.operational_mapping = action
                elif action:
                    proposal.operational_mapping = None
                    proposal.unsupported_suggestions.append(action)

                # Fall back to deterministic if LLM produced nothing
                if not proposal.plain_language and issue_type in det_map:
                    proposals.append(det_map[issue_type])
                else:
                    proposals.append(proposal)

            except Exception:
                # Fall back to deterministic on LLM failure
                if issue_type in det_map:
                    proposals.append(det_map[issue_type])

        return RemediationProposalBundle(proposals=proposals)

    def _llm_propose(
        self,
        issue_type: str,
        columns: Sequence[str],
        decision: QualityDecision,
    ) -> dict[str, Any]:
        request = RemediationProposalRequest(
            issue_type=issue_type,
            affected_columns=list(columns),
            issue_metadata=decision.issue_metadata.get(issue_type, {}),
            decision=decision.decision,
        )

        messages = build_json_messages(
            system_instruction=REMEDIATION_SYSTEM,
            payload=request.model_dump(mode="json"),
        )

        llm_request = LLMRequest(
            provider="litellm",
            model=self._model,
            prompt_version=PROMPT_VERSION,
            messages=messages,
            metadata={"task": "remediation"},
        )

        import json
        response = self._client.complete(llm_request)
        data = json.loads(response.content)

        descriptions: dict[str, str] = {
            "missing_values": "impute",
            "duplicate_rows": "remove_duplicates",
            "constant_column": "drop_column",
            "outliers": "clip",
            "high_skewness": "log_transform",
            "high_correlation": "drop_column",
            "range_violation": "clip",
            "pattern_violation": "cast_type",
            "pii_detected": "mask_pii",
            "anomaly_score": "remove_anomalies",
            "type_mismatch": "cast_type",
            "zero_value": "flag_nulls",
        }

        return {
            "action": descriptions.get(issue_type),
            "risk_level": data.get("risk_level", "medium"),
            "description": "; ".join(data.get("proposals", [])) or RemediationProposalEngine._description_for_issue(issue_type, columns),
        }


class RemediationProposalEngine:
    def propose(
        self,
        *,
        decision: QualityDecision,
        action_plan: ActionPlan | None,
    ) -> RemediationProposalBundle:
        proposals: list[RemediationProposal] = []

        for issue_type, cols in decision.issue_map.items():
            proposal = self._proposal_for_issue(
                issue_type=issue_type,
                columns=cols,
                severity=decision.severity_level,
                decision=decision.decision,
                action_plan=action_plan,
            )
            if proposal is not None:
                proposals.append(proposal)

        return RemediationProposalBundle(proposals=proposals)

    def _map_issue_to_action(self, issue_type: str) -> str | None:
        mapping: dict[str, str] = {
            "missing_values": "impute",
            "duplicate_rows": "remove_duplicates",
            "constant_column": "drop_column",
            "outliers": "clip",
            "high_skewness": "log_transform",
            "high_correlation": "drop_column",
            "range_violation": "clip",
            "pattern_violation": "cast_type",
            "pii_detected": "mask_pii",
            "anomaly_score": "remove_anomalies",
            "type_mismatch": "cast_type",
            "zero_value": "flag_nulls",
        }
        return mapping.get(issue_type)

    def _proposal_for_issue(
        self,
        *,
        issue_type: str,
        columns: Sequence[str],
        severity: str,
        decision: str,
        action_plan: ActionPlan | None,
    ) -> RemediationProposal | None:
        mapped = self._map_issue_to_action(issue_type)

        proposal = RemediationProposal(
            issue_type=issue_type,
            proposed_action=mapped,
            operational_mapping=mapped if mapped in ALLOWED_ACTIONS else None,
            column=columns[0] if columns else None,
            risk_level=self._risk_from_severity(severity, decision),
            requires_approval=(
                action_plan.requires_human if action_plan else True
            ),
            plain_language=self._description_for_issue(issue_type, columns),
        )

        if mapped and mapped not in ALLOWED_ACTIONS:
            proposal.operational_mapping = None
            proposal.unsupported_suggestions.append(mapped)

        return proposal

    @staticmethod
    def _risk_from_severity(
        severity: str, decision: str
    ) -> Literal["low", "medium", "high"]:
        if decision == "FAIL":
            return "high"
        if severity in ("CRITICAL", "HIGH"):
            return "high"
        if severity == "MEDIUM":
            return "medium"
        return "low"

    @staticmethod
    def _description_for_issue(issue_type: str, columns: Sequence[str]) -> str:
        descriptions: dict[str, str] = {
            "missing_values": "Replace nulls via median/mode imputation.",
            "duplicate_rows": "Drop exact duplicate rows.",
            "constant_column": "Remove columns with no variance.",
            "outliers": "Clip extreme values based on IQR.",
            "high_skewness": "Apply log transformation to reduce skew.",
            "high_correlation": "Remove one of the highly correlated columns.",
            "range_violation": "Clip values to allowed range.",
            "pattern_violation": "Cast column to expected type or format.",
            "pii_detected": "Mask personally identifiable information.",
            "anomaly_score": "Drop rows flagged as anomalous by Isolation Forest.",
            "type_mismatch": "Cast column to the profile-suggested type.",
            "zero_value": "Flag rows where expected numeric data is zero.",
        }
        base = descriptions.get(issue_type, f"Address {issue_type}.")
        if columns:
            base += f" Affected: {', '.join(columns[:3])}."
        return base
