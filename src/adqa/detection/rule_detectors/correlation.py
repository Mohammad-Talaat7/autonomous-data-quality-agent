# correlation.py

from ...config.model import DetectionThresholds
from ..base import CrossColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class CorrelationDetector(CrossColumnDetector):
    name = "CorrelationDetector"
    dimension = QualityDimension.CONSISTENCY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = thresholds.correlation_threshold if thresholds else 0.9

    def detect(self, context: DetectionContext) -> list[DetectionResult]:
        matrix = context.correlation_matrix
        if matrix is None:
            return []

        results = []
        # matrix is Mapping[tuple[str, str], float]
        for (col1, col2), corr in matrix.items():
            if col1 == col2:
                continue

            if abs(corr) > self.threshold:
                results.append(
                    DetectionResult(
                        detector_name=self.name,
                        issue_type="high_correlation",
                        columns=[col1, col2],
                        scope="cross_column",
                        severity_hint=abs(corr),
                        metrics={"observed_value": corr, "threshold": self.threshold},
                        description=f"{col1} and {col2} highly correlated ({corr:.2f})",
                    )
                )
        return results
