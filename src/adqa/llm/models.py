from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LLMMessage(StrictModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMRequest(StrictModel):
    provider: str = "litellm"
    model: str
    prompt_version: str
    trace_id: str | None = None
    messages: list[LLMMessage]
    temperature: float = 0.0
    timeout_seconds: int = 30
    api_key: str | None = None
    api_base: str | None = None
    service_tier: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def input_hash(self) -> str:
        payload = {
            "provider": self.provider,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "trace_id": self.trace_id,
            "messages": [m.model_dump(mode="json") for m in self.messages],
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }
        data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(data.encode("utf-8")).hexdigest()


class LLMResponse(StrictModel):
    provider: str
    model: str
    prompt_version: str
    trace_id: str | None = None
    input_hash: str
    output_hash: str
    content: str
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)


class DatasetSummary(StrictModel):
    row_count: int
    column_count: int
    duplicate_row_ratio: float
    total_null_ratio: float
    columns: list[str]
    correlations_present: bool


class ActionPlanSummary(StrictModel):
    summary: str
    requires_human: bool
    action_types: list[str]


class StructuredLLMResult(StrictModel):
    provider: str
    model: str
    prompt_version: str
    trace_id: str | None = None
    input_hash: str
    output_hash: str
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)


class ExplanationRequest(StrictModel):
    trace_id: str | None = None
    decision: str
    score: float
    severity_level: str
    dimension_breakdown: dict[str, float]
    issue_breakdown: dict[str, float]
    dominant_issues: list[str]
    affected_columns: list[str]
    issue_map: dict[str, list[str]]
    issue_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)
    reason_codes: list[str]
    dataset_summary: DatasetSummary
    action_plan: ActionPlanSummary | None = None


class ExplanationResponse(StructuredLLMResult):
    short_summary: str
    top_issues: list[str]
    affected_columns: list[str]
    why_decision: list[str]
    recommended_next_steps: list[str]
    uncertainty: str | None = None


class SemanticClassificationRequest(StrictModel):
    trace_id: str | None = None
    column_name: str
    column_summary: dict[str, Any]
    allowed_labels: list[str]


class SemanticClassificationResponse(StructuredLLMResult):
    label: str
    rationale: str


class RemediationProposalRequest(StrictModel):
    trace_id: str | None = None
    issue_type: str
    affected_columns: list[str]
    issue_metadata: dict[str, Any] = Field(default_factory=dict)
    decision: str


class RemediationProposalResponse(StructuredLLMResult):
    proposals: list[str]
    risk_level: Literal["low", "medium", "high"]
    requires_human_review: bool = True
