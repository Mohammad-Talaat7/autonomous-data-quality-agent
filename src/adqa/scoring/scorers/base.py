from abc import ABC, abstractmethod

from ..models import NormalizedDetection, Score


class BaseScorer(ABC):
    @abstractmethod
    def compute(self, detection: NormalizedDetection) -> Score:
        pass
