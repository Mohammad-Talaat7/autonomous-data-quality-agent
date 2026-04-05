from ..models import NormalizedDetection, Score
from ..thresholds import Thresholds


class RuleScorer:
    def __init__(self, weight_map: dict[str, float] | None = None) -> None:
        self.weight_map = weight_map or {}

    def _get_weight(self, detection: NormalizedDetection) -> float:
        return float(self.weight_map.get(detection.rule_id, Thresholds.DEFAULT_WEIGHT))

    def compute(self, detection: NormalizedDetection) -> Score:
        weight = self._get_weight(detection)

        # Basic formula: severity * confidence * weight
        final_score = detection.severity * detection.confidence * weight

        return Score(
            detector_id=detection.detector_id,
            rule_id=detection.rule_id,
            issue_type=detection.issue_type,
            dimension=detection.dimension,
            column=detection.column,
            severity=detection.severity,
            confidence=detection.confidence,
            weight=weight,
            final_score=final_score,
            metadata=detection.metadata,
        )
