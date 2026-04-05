# detection/base.py

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from .context import DetectionContext
from .results import DetectionResult, MLEvidence

__all__ = [
    "DetectorScope",
    "QualityDimension",
    "BaseDetector",
    "ColumnDetector",
    "DatasetDetector",
    "CrossColumnDetector",
    "BaseMLDetector",
    "DetectionContext",
    "DetectionResult",
    "MLEvidence",
]


class DetectorScope(StrEnum):
    COLUMN = "column"
    DATASET = "dataset"
    CROSS_COLUMN = "cross_column"


class QualityDimension(StrEnum):
    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"
    CONSISTENCY = "consistency"
    INTEGRITY = "integrity"
    TIMELINESS = "timeliness"
    ACCURACY = "accuracy"
    PRIVACY = "privacy"
    BIAS = "bias"


# =========================
# Rule-Based
# =========================


class BaseDetector(ABC):
    name: str
    scope: DetectorScope
    dimension: QualityDimension

    @abstractmethod
    def detect(self, context: DetectionContext) -> list[DetectionResult]:
        pass


class ColumnDetector(BaseDetector):
    scope = DetectorScope.COLUMN

    def detect(self, context: DetectionContext) -> list[DetectionResult]:
        results = []
        for column in context.column_profiles:
            results.extend(self.detect_column(column, context))
        return results

    @abstractmethod
    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        pass


class DatasetDetector(BaseDetector):
    scope = DetectorScope.DATASET


class CrossColumnDetector(BaseDetector):
    scope = DetectorScope.CROSS_COLUMN


# =========================
# ML-Based
# =========================


class BaseMLDetector(ABC):
    name: str
    dimension: QualityDimension = QualityDimension.ACCURACY  # Default for ML signals
    requires_history: bool = False

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def run_model(self, context: DetectionContext) -> list[MLEvidence]:
        pass
