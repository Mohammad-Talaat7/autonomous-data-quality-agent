from __future__ import annotations

from typing import Any

from ...llm.client import BaseLLMClient
from ...llm.models import LLMRequest
from ...llm.prompts import build_json_messages
from ..base import BaseMLDetector, DetectionContext, QualityDimension
from ..results import MLEvidence


class AnomalousSchemaDetector(BaseMLDetector):
    """AI-based schema anomaly detection using column profile summaries."""

    name = "AnomalousSchemaDetector"
    dimension = QualityDimension.ACCURACY
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
                evidence = self._check_column(col_name, profile, context)
                if evidence is not None:
                    results.append(evidence)
            except Exception:
                continue
        return results

    def _check_column(
        self, col_name: str, profile: Any, context: DetectionContext
    ) -> MLEvidence | None:
        warnings: dict[str, Any] = {}

        structural = getattr(profile, "structural_metrics", None)
        if structural is not None:
            if getattr(structural, "null_ratio", 0.0) > 0.95:
                warnings["warning_null_ratio"] = structural.null_ratio
            if getattr(structural, "unique_ratio", 0.0) < 0.001:
                warnings["warning_low_cardinality"] = structural.unique_ratio

        if not warnings:
            return None

        warnings["column"] = col_name

        PROMPT_VERSION = "adqa.detection.anomalous_schema.v1"
        SYSTEM_INSTRUCTION = (
            "You are a schema anomaly detector. "
            "Column summary signals are provided. "
            "Return strict JSON with keys: anomaly_detected (bool), description (str)."
        )

        import json

        messages = build_json_messages(
            system_instruction=SYSTEM_INSTRUCTION,
            payload=warnings,
        )
        request = LLMRequest(
            provider="litellm",
            model=self._model,
            prompt_version=PROMPT_VERSION,
            messages=messages,
            metadata={"task": "anomalous_schema"},
        )

        try:
            response = self._client.complete(request)
            data = json.loads(response.content)
            if not data.get("anomaly_detected", False):
                return None
        except Exception:
            return None

        return MLEvidence(
            model_name=self.name,
            signal_type="anomalous_schema",
            column=col_name,
            score=0.85,
            confidence=0.85,
            metadata={
                "description": data.get("description", ""),
                "signals": warnings,
            },
        )
