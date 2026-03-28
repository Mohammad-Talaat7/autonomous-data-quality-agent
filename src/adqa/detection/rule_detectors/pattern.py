# pattern.py

import re

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class PatternDetector(ColumnDetector):
    name = "PatternDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(
        self,
        thresholds: DetectionThresholds | None = None,
        pattern: str = r".+@.+\..+",
    ) -> None:
        self.pattern = re.compile(pattern)
        self.threshold = thresholds.pattern_match_threshold if thresholds else 0.8

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        if context.raw_data_sample is None:
            return []

        values = context.raw_data_sample[column].dropna().astype(str)

        if len(values) == 0:
            return []

        matches = values.apply(lambda x: bool(self.pattern.match(x)))
        ratio = matches.mean()

        if ratio < self.threshold:
            # Pattern violation means match ratio is low
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="pattern_violation",
                    column=column,
                    severity_hint=1 - ratio,
                    metrics={"observed_value": ratio, "threshold": self.threshold},
                    description=f"{column} violates expected pattern"
                    + " (match ratio: {ratio:.2%})",
                )
            ]
        return []
