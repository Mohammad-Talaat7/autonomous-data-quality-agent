# adqa/explanation/engine.py
from __future__ import annotations

from ..config import LLMConfig
from ..detection.results import DetectionResultBundle
from ..execution.models import ActionPlan
from ..llm.client import BaseLLMClient
from ..llm.models import ActionPlanSummary, DatasetSummary, ExplanationRequest
from ..profiling.models.dataset_profile import DatasetProfile
from ..scoring.models import AggregatedScore, QualityDecision
from ..trace.reasoning import collect_reason_codes
from .models import ADQAExplanation
from .prompts import build_explanation_prompt


class ExplanationEngine:
    def __init__(self, *, client: BaseLLMClient, config: LLMConfig) -> None:
        self._client = client
        self._config = config

    def explain(
        self,
        *,
        trace_id: str | None,
        tracer: object | None = None,
        decision: QualityDecision,
        scores: AggregatedScore,
        detections: DetectionResultBundle,
        dataset_profile: DatasetProfile,
        action_plan: ActionPlan | None,
    ) -> ADQAExplanation:
        if tracer is not None and hasattr(self._client, "_tracer"):
            self._client._tracer = tracer
        request = ExplanationRequest(
            trace_id=trace_id,
            decision=decision.decision,
            score=decision.score,
            severity_level=decision.severity_level,
            dimension_breakdown=decision.dimension_breakdown,
            issue_breakdown=scores.issue_breakdown,
            dominant_issues=decision.dominant_issues,
            affected_columns=decision.affected_columns,
            issue_map=decision.issue_map,
            issue_metadata=decision.issue_metadata,
            reason_codes=collect_reason_codes(detections),
            dataset_summary=DatasetSummary(
                row_count=dataset_profile.metadata.row_count,
                column_count=dataset_profile.metadata.column_count,
                duplicate_row_ratio=dataset_profile.metadata.duplicate_row_ratio,
                total_null_ratio=dataset_profile.metadata.total_null_ratio,
                columns=[column.name for column in dataset_profile.columns],
                correlations_present=dataset_profile.correlations is not None,
            ),
            action_plan=(
                ActionPlanSummary(
                    summary=action_plan.summary,
                    requires_human=action_plan.requires_human,
                    action_types=[action.action_type for action in action_plan.actions],
                )
                if action_plan is not None
                else None
            ),
        )

        llm_request = build_explanation_prompt(
            request,
            provider=self._config.provider,
            model=self._config.model or "",
            temperature=self._config.temperature,
            timeout_seconds=self._config.timeout_seconds,
            redact_samples=self._config.redact_samples,
            max_input_chars=self._config.max_input_chars,
            api_key=getattr(self._config, "api_key", None),
            api_base=getattr(self._config, "api_base", None),
        )
        return self._client.complete_structured(llm_request, ADQAExplanation)
