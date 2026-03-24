# detection/__init__.py

from .engine import DetectionEngine
from .registry_setup import build_registry

__all__ = ["DetectionEngine", "build_registry"]
