# adqa/chat/session.py

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal

from ..llm.client import BaseLLMClient
from ..llm.models import LLMMessage, LLMRequest

if TYPE_CHECKING:
    from ..core.result import ADQAResult
    from ..explanation.engine import ExplanationEngine
    from ..explanation.remediation import RemediationProposalEngine

CHAT_PROMPT_VERSION = "adqa.chat.v1"
CHAT_SYSTEM_INSTRUCTION = (
    "You are ADQA, an autonomous data quality agent. "
    "Answer the user's questions using only the structured analysis results provided. "
    "Be concise. If you are uncertain, say so."
)


class ChatSession:
    def __init__(
        self,
        *,
        client: BaseLLMClient,
        model: str = "",
        provider: str = "",
        explanation_engine: ExplanationEngine | None = None,
        remediation_engine: RemediationProposalEngine | None = None,
        result: ADQAResult | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._provider = provider
        self._explanation = explanation_engine
        self._remediation = remediation_engine
        self._result = result
        self._history: list[LLMMessage] = []

    def inject_result(self, result: ADQAResult) -> None:
        self._result = result

    def add_message(
        self, role: Literal["system", "user", "assistant"], content: str
    ) -> None:
        self._history.append(LLMMessage(role=role, content=content))

    def send(self, user_message: str) -> str:
        if not self._result:
            return "No analysis result available. Please run an analysis first."

        lower = user_message.strip().lower()

        if lower.startswith("explain") and self._explanation is not None:
            return self._handle_explain()
        if lower.startswith("fix") or lower.startswith("remediate"):
            return self._handle_remediate()
        if lower.startswith("why") or lower.startswith("cause"):
            return self._handle_root_cause()

        return self._chat(user_message)

    def _handle_explain(self) -> str:
        if not self._result or not self._result.decision:
            return "No analysis result to explain."
        explanation = getattr(self._result, "explanation", None)
        if explanation:
            return (
                f"Summary: {explanation.short_summary}\n"
                f"Top issues: {', '.join(explanation.top_issues)}\n"
                f"Why: {'; '.join(explanation.why_decision)}\n"
                f"Next steps: {'; '.join(explanation.recommended_next_steps)}"
            )
        return "Explanation unavailable for this result."

    def _handle_remediate(self) -> str:
        if not self._result or not self._result.decision:
            return "No analysis result to remediate."
        if self._remediation is None:
            return "Remediation agent not configured."
        try:
            bundle = self._remediation.propose(
                decision=self._result.decision,
                action_plan=self._result.plan,
            )
            lines = []
            for p in bundle.proposals:
                action = p.operational_mapping or p.proposed_action or "review"
                lines.append(f"- {p.issue_type}: {action} ({p.plain_language})")
            return "Proposed fixes:\n" + "\n".join(lines)
        except Exception as exc:
            return f"Remediation proposal failed: {exc}"

    def _handle_root_cause(self) -> str:
        if not self._result:
            return "No analysis result available."
        try:
            from ..explanation.root_cause import RootCauseEngine

            engine = RootCauseEngine()
            if (
                not self._result.detections
                or not self._result.scores
                or not self._result.profiles
            ):
                return "No root causes identified (incomplete analysis)."
            causes = list(
                engine.analyse(
                    detections=self._result.detections,
                    scores=self._result.scores,
                    dataset_profile=self._result.profiles.dataset_profile,
                )
            )
            if not causes:
                return "No root causes identified."
            lines = []
            for c in causes:
                evidence = "; ".join(c.evidence[:2])
                lines.append(
                    f"- {c.cause} (confidence: {c.confidence:.2f}): {evidence}"
                )
            return "Possible causes:\n" + "\n".join(lines)
        except Exception as exc:
            return f"Root cause analysis failed: {exc}"

    def _chat(self, user_message: str) -> str:
        self.add_message("user", user_message)

        context_text = "No analysis context available."
        if self._result and self._result.decision:
            import json

            context_text = "Analysis result context:\n" + json.dumps(
                self._result.decision.to_dict(), default=str
            )

        messages = [
            LLMMessage(role="system", content=CHAT_SYSTEM_INSTRUCTION),
            LLMMessage(role="system", content=context_text),
            *self._history,
        ]

        try:
            api_key = None
            api_base = None
            # Forward credentials when the engine was built with an LLMConfig
            service_tier = None
            config = (
                getattr(self._explanation, "_config", None)
                if self._explanation
                else None
            )
            chat_provider = "litellm"
            if config is not None:
                api_key = getattr(config, "api_key", None)
                api_base = getattr(config, "api_base", None)
                service_tier = getattr(config, "service_tier", None)
                chat_provider = getattr(config, "provider", None) or chat_provider
            # Fall back to env vars (set by the GUI settings page)
            if not api_key:
                api_key = os.environ.get("OPENAI_API_KEY") or None
            if not api_base:
                api_base = os.environ.get("OPENAI_API_BASE") or None
            request = LLMRequest(
                provider=chat_provider,
                model=self._model or "",
                prompt_version=CHAT_PROMPT_VERSION,
                messages=messages,
                api_key=api_key,
                api_base=api_base,
                service_tier=service_tier,
                metadata={"task": "chat"},
            )
            response = self._client.complete(request)
            self.add_message("assistant", response.content)
            return response.content
        except Exception as exc:
            return f"Chat error: {exc}"
