# tests/detection/test_llm_semantic.py

"""Tests for LLMSemanticClassifier augmenter."""

import json
from hashlib import sha256

from adqa.detection.context import DetectionContext
from adqa.detection.ml_detectors.llm_semantic import LLMSemanticClassifier
from adqa.llm.client import BaseLLMClient
from adqa.llm.models import (
    LLMRequest,
    LLMResponse,
)
from adqa.profiling.models.column_profile import ColumnProfile, LogicalType
from adqa.profiling.models.dataset_profile import DatasetMetadata, DatasetProfile
from adqa.profiling.models.metrics import StructuralMetrics


class FakeSemanticLLMClient(BaseLLMClient):
    def __init__(self, label: str, confidence: float, fail: bool = False):
        self._label = label
        self._confidence = confidence
        self._fail = fail

    def complete(self, request: LLMRequest) -> LLMResponse:
        if self._fail:
            raise RuntimeError("provider down")
        content = json.dumps(
            {
                "label": self._label,
                "rationale": f"Column matches {self._label} pattern.",
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
            confidence=self._confidence,
        )


def _make_context():
    structural = StructuralMetrics(
        null_ratio=0.0,
        unique_ratio=0.9,
        duplicate_ratio=0.0,
        memory_usage_bytes=1024,
    )
    col = ColumnProfile(
        name="email_col",
        dtype="str",
        logical_type=LogicalType.TEXT,
        structural_metrics=structural,
    )
    metadata = DatasetMetadata(
        row_count=100,
        column_count=3,
        duplicate_row_ratio=0.0,
        memory_usage_bytes=4096,
        total_null_ratio=0.01,
        type_distribution={"str": 3},
    )
    profile = DatasetProfile(metadata=metadata, columns=(col,), correlations=None)
    return DetectionContext(
        dataset_profile=profile,
        column_profiles={"email_col": col},
        ml_profiles=None,
        correlation_matrix=None,
        raw_data_sample=None,
        historical_profiles=None,
    )


def test_enabled_path_produces_evidence():
    client = FakeSemanticLLMClient(label="email", confidence=0.82)
    detector = LLMSemanticClassifier(client=client, enabled=True)
    context = _make_context()

    evidence_list = detector.run_model(context)

    assert len(evidence_list) == 1
    ev = evidence_list[0]
    assert ev.signal_type == "llm_semantic_label"
    assert ev.column == "email_col"
    assert ev.score == 0.82
    assert ev.metadata["llm_label"] == "email"


def test_disabled_path_returns_empty():
    client = FakeSemanticLLMClient(label="email", confidence=0.82)
    detector = LLMSemanticClassifier(client=client, enabled=False)
    context = _make_context()

    evidence_list = detector.run_model(context)

    assert evidence_list == []


def test_client_failure_returns_empty():
    client = FakeSemanticLLMClient(label="email", confidence=0.82, fail=True)
    detector = LLMSemanticClassifier(client=client, enabled=True)
    context = _make_context()

    evidence_list = detector.run_model(context)

    assert evidence_list == []
