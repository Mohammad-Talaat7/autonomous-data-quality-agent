# tests/llm/test_client.py
import json
from hashlib import sha256

from adqa.llm.client import BaseLLMClient
from adqa.llm.models import ExplanationResponse, LLMMessage, LLMRequest, LLMResponse


class FakeLLMClient(BaseLLMClient):
    def complete(self, request: LLMRequest) -> LLMResponse:
        content = json.dumps(
            {
                "short_summary": "Quality risk is driven by missing values.",
                "top_issues": ["missing_values"],
                "affected_columns": ["email"],
                "why_decision": ["The null ratio crossed the configured threshold."],
                "recommended_next_steps": ["Fix the source feed and re-run ADQA."],
                "uncertainty": "Explanation is based only on deterministic results.",
            }
        )
        return LLMResponse(
            provider=request.provider,
            model=request.model,
            prompt_version=request.prompt_version,
            trace_id=request.trace_id,
            input_hash=request.input_hash(),
            output_hash=sha256(content.encode("utf-8")).hexdigest(),
            content=content,
            confidence=0.91,
        )


def test_complete_structured_validates_payload():
    client = FakeLLMClient()
    request = LLMRequest(
        model="gpt-4o-mini",
        prompt_version="adqa.explanation.v1",
        messages=[LLMMessage(role="system", content="Return JSON")],
    )

    response = client.complete_structured(
        request,
        ExplanationResponse,
    )

    assert response.short_summary.startswith("Quality risk")
    assert response.confidence == 0.91
