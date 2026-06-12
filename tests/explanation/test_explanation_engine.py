# tests/explanation/test_explanation_engine.py

import json
from hashlib import sha256

import pandas as pd

from adqa.config import ADQAConfig
from adqa.core.api import ADQA
from adqa.llm.client import BaseLLMClient
from adqa.llm.models import LLMRequest, LLMResponse


class FakeLLMClient(BaseLLMClient):
    def complete(self, request: LLMRequest) -> LLMResponse:
        content = json.dumps(
            {
                "short_summary": "Missing values drive the warning.",
                "top_issues": ["missing_values"],
                "affected_columns": ["email"],
                "why_decision": ["Configured completeness threshold was exceeded."],
                "recommended_next_steps": ["Repair missing emails at the source."],
                "uncertainty": "No raw row data was sent to the model.",
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
            confidence=0.88,
        )


class FailingLLMClient(BaseLLMClient):
    def complete(self, request: LLMRequest) -> LLMResponse:
        raise RuntimeError("provider unavailable")


def test_explanation_disabled_by_default():
    df = pd.DataFrame({"email": ["a@x.com", None, "c@x.com"]})

    result = ADQA.from_df(df).analyze()

    assert result.explanation is None
    assert result.warnings == []


def test_explanation_generated_with_fake_client():
    df = pd.DataFrame({"email": ["a@x.com", None, None]})
    config = ADQAConfig(
        llm={"enabled": True, "model": "gpt-4o-mini"},
        tracing_enabled=True,
    )

    result = ADQA.from_df(df, config=config, llm_client=FakeLLMClient()).analyze()

    assert result.explanation is not None
    assert result.explanation.short_summary == "Missing values drive the warning."
    assert "missing_values" in result.explanation.top_issues


def test_explanation_failure_does_not_break_analysis():
    df = pd.DataFrame({"email": ["a@x.com", None, None]})
    config = ADQAConfig(llm={"enabled": True, "model": "gpt-4o-mini"})

    result = ADQA.from_df(df, config=config, llm_client=FailingLLMClient()).analyze()

    assert result.error is None
    assert result.explanation is None
    assert result.warnings
    assert "LLM explanation failed" in result.warnings[0]
