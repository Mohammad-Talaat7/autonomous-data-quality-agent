# detection/registry.py


from typing import Any

from .base import BaseDetector, BaseMLDetector


class DetectorRegistry:
    def __init__(self) -> None:
        self._rule_detectors: list[type[BaseDetector]] = []
        self._ml_detectors: list[type[BaseMLDetector]] = []

    # =========================
    # Registration
    # =========================

    def register_rule(self, detector_cls: type[BaseDetector]) -> None:
        self._rule_detectors.append(detector_cls)

    def register_ml(self, detector_cls: type[BaseMLDetector]) -> None:
        self._ml_detectors.append(detector_cls)

    # =========================
    # Instantiation
    # =========================

    def create_rule_detectors(self, **kwargs: Any) -> list[BaseDetector]:
        return [cls(**kwargs) for cls in self._rule_detectors]

    def create_ml_detectors(self, **kwargs: Any) -> list[BaseMLDetector]:
        return [cls(**kwargs) for cls in self._ml_detectors]

    # =========================
    # Introspection
    # =========================

    def list_rule_detectors(self) -> list[str]:
        return [cls.__name__ for cls in self._rule_detectors]

    def list_ml_detectors(self) -> list[str]:
        return [cls.__name__ for cls in self._ml_detectors]
