# adqa/explanation/prompts.py
from __future__ import annotations

from ..llm.models import ExplanationRequest, LLMRequest
from ..llm.prompts import build_json_messages
from ..llm.redaction import sanitize_payload

PROMPT_VERSION = "adqa.explanation.v1"

SYSTEM_INSTRUCTION = """
You are ADQA's explanation layer.
Explain only the deterministic findings provided.
Do not invent detectors, scores, or actions.
Return strict JSON with these keys:
short_summary, top_issues, affected_columns, why_decision,
recommended_next_steps, uncertainty.
""".strip()


def build_explanation_prompt(
    request: ExplanationRequest,
    *,
    provider: str,
    model: str,
    temperature: float,
    timeout_seconds: int,
    redact_samples: bool,
    max_input_chars: int,
    api_key: str | None = None,
    api_base: str | None = None,
) -> LLMRequest:
    payload = sanitize_payload(
        request.model_dump(mode="json"),
        redact_samples=redact_samples,
        max_chars=max_input_chars,
    )
    return LLMRequest(
        provider=provider,
        model=model,
        prompt_version=PROMPT_VERSION,
        trace_id=request.trace_id,
        messages=build_json_messages(
            system_instruction=SYSTEM_INSTRUCTION,
            payload=payload,
        ),
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        api_key=api_key,
        api_base=api_base,
        metadata={"task": "explanation"},
    )
