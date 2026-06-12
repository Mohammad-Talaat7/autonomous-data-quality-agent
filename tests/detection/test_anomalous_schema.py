# tests/detection/test_anomalous_schema.py

"""Tests for AnomalousSchemaDetector."""

import json
from hashlib import sha256

from adqa.detection.ml_detectors.anomalous_schema import AnomalousSchemaDetector
from adqa.detection.context import DetectionContext
from adqa.llm.client import BaseLLMClient
from adqa.llm.models import LLMRequest, LLMResponse
from adqa.profiling.models.column_profile import ColumnProfile, LogicalType
from adqa.profiling.models.dataset_profile import DatasetMetadata, DatasetProfile
from adqa.profiling.models.metrics import StructuralMetrics


class AnomalyMockClient(BaseLLMClient):
    def __init__(self, anomaly: bool = True):
        super().__init__()
        self._anomaly = anomaly

    def complete(self, request: LLMRequest) -> LLMResponse:
        content = json.dumps({
            "anomaly_detected": self._anomaly,
            "description": "Column appears nearly empty." if self._anomaly else "ok",
        })
        return LLMResponse(
            provider=request.provider,
            model=request.model,
            prompt_version=request.prompt_version,
            trace_id=request.trace_id,
            input_hash=request.input_hash(),
            output_hash=sha256(content.encode("utf-8")).hexdigest(),
            content=content,
        )


def _make_context(null_ratio=0.98, unique_ratio=0.5):
    structural = StructuralMetrics(
        null_ratio=null_ratio,
        unique_ratio=unique_ratio,
        duplicate_ratio=0.0,
        memory_usage_bytes=1024,
    )
    col = ColumnProfile(
        name="col_x",
        dtype="str",
        logical_type=LogicalType.TEXT,
        structural_metrics=structural,
    )
    metadata = DatasetMetadata(
        row_count=100,
        column_count=3,
        duplicate_row_ratio=0.0,
        memory_usage_bytes=4096,
        total_null_ratio=0.5,
        type_distribution={"str": 3},
    )
    profile = DatasetProfile(metadata=metadata, columns=(col,), correlations=None)
    return DetectionContext(
        dataset_profile=profile,
        column_profiles={"col_x": col},
        ml_profiles=None,
        correlation_matrix=None,
        raw_data_sample=None,
        historical_profiles=None,
    )


def test_anomaly_detected():
    client = AnomalyMockClient(anomaly=True)
    detector = AnomalousSchemaDetector(client=client, enabled=True)
    context = _make_context(null_ratio=0.99)

    evidence_list = detector.run_model(context)
    assert len(evidence_list) == 1
    assert evidence_list[0].signal_type == "anomalous_schema"


def test_no_anomaly():
    client = AnomalyMockClient(anomaly=False)
    detector = AnomalousSchemaDetector(client=client, enabled=True)
    context = _make_context(null_ratio=0.99)

    evidence_list = detector.run_model(context)
    assert evidence_list == []


def test_disabled_returns_empty():
    client = AnomalyMockClient(anomaly=True)
    detector = AnomalousSchemaDetector(client=client, enabled=False)
    context = _make_context()

    evidence_list = detector.run_model(context)
    assert evidence_list == []


def test_no_signals_skips():
    client = AnomalyMockClient(anomaly=True)
    detector = AnomalousSchemaDetector(client=client, enabled=True)
    context = _make_context(null_ratio=0.1, unique_ratio=0.8)

    evidence_list = detector.run_model(context)
    assert evidence_list == []
