from __future__ import annotations

from typing import Any

from ...llm.client import BaseLLMClient
from ...llm.models import SemanticClassificationRequest, SemanticClassificationResponse
from ...llm.redaction import sanitize_payload
from ..base import BaseMLDetector, DetectionContext, QualityDimension
from ..context import DetectionContext
from ..results import MLEvidence


class LLMSemanticClassifier(BaseMLDetector):
    name = "LLMSemanticClassifier"
    dimension = QualityDimension.VALIDITY

    def __init__(
        self,
        *,
        client: BaseLLMClient,
        model: str = "",
        enabled: bool = True,
        thresholds: Any = None,
        **kwargs: Any,
    ) -> None:
        self._client = client
        self._model = model
        self._enabled = enabled

    def run_model(self, context: DetectionContext) -> list[MLEvidence]:
        if not self._enabled:
            return []

        results: list[MLEvidence] = []
        for col_name, profile in context.column_profiles.items():
            try:
                evidence = self._classify_column(col_name, profile, context)
                if evidence is not None:
                    results.append(evidence)
            except Exception:
                continue
        return results

    def _classify_column(
        self, col_name: str, profile: Any, context: DetectionContext
    ) -> MLEvidence | None:
        column_summary: dict[str, Any] = {
            "name": col_name,
            "dtype": str(getattr(profile, "dtype", "")),
            "logical_type": getattr(
                getattr(profile, "logical_type", None), "value", "unknown"
            ),
        }
        if hasattr(profile, "structural_metrics") and profile.structural_metrics:
            column_summary["null_ratio"] = profile.structural_metrics.null_ratio
            column_summary["unique_ratio"] = profile.structural_metrics.unique_ratio

        request = SemanticClassificationRequest(
            column_name=col_name,
            column_summary=sanitize_payload(column_summary),
            allowed_labels=self._allowed_labels(),
        )

        try:
            response = self._client.complete_structured(
                self._build_llm_request(request),
                SemanticClassificationResponse,
            )
        except Exception:
            return None

        return MLEvidence(
            model_name=self.name,
            signal_type="llm_semantic_label",
            column=col_name,
            score=response.confidence,
            confidence=response.confidence,
            metadata={
                "llm_label": response.label,
                "rationale": response.rationale,
            },
        )

    def _build_llm_request(self, request: SemanticClassificationRequest) -> Any:
        from ...llm.models import LLMRequest
        from ...llm.prompts import build_json_messages

        PROMPT_VERSION = "adqa.detection.llm_semantic.v1"
        SYSTEM_INSTRUCTION = (
            "You are a semantic column classifier for data quality. "
            "Given a column name, type, and summary statistics, assign exactly one "
            "label from the allowed list. Return strict JSON with keys: label, rationale."
        )
        return LLMRequest(
            provider="litellm",
            model=self._model,
            prompt_version=PROMPT_VERSION,
            messages=build_json_messages(
                system_instruction=SYSTEM_INSTRUCTION,
                payload=request.model_dump(mode="json"),
            ),
        )

    @staticmethod
    def _allowed_labels() -> list[str]:
        return [
            "email",
            "phone",
            "identifier",
            "target",
            "timestamp",
            "country_code",
            "free_text",
            "numeric_measurement",
            "categorical_label",
            "boolean_flag",
            "unknown",
        ]
