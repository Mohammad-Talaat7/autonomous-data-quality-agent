# pattern.py

import re

from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class PatternDetector(ColumnDetector):
    """
    Smarter Pattern Detector that only validates columns with semantic intent.
    """

    name = "PatternDetector"
    dimension = QualityDimension.VALIDITY

    def __init__(
        self,
        thresholds: DetectionThresholds | None = None,
        pattern: str = r".+@.+\..+",
        target_semantic: str = "email",
    ) -> None:
        self.pattern = re.compile(pattern)
        self.threshold = thresholds.pattern_match_threshold if thresholds else 0.8
        self.target_semantic = target_semantic

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        if context.raw_data_sample is None:
            return []

        profile = context.get_column(column)

        # Check if the target semantic tag is in the tags tuple
        has_tag = False
        if hasattr(profile, "semantic_tags") and profile.semantic_tags:
            has_tag = any(
                tag.value == self.target_semantic for tag in profile.semantic_tags
            )

        if not has_tag:
            return []

        values = context.raw_data_sample[column].dropna().astype(str)
        if len(values) == 0:
            return []

        matches = values.apply(lambda x: bool(self.pattern.match(x)))
        ratio = float(matches.mean())

        if ratio < self.threshold:
            return [
                DetectionResult(
                    detector_name=self.name,
                    issue_type="pattern_violation",
                    column=column,
                    severity_hint=1.0 - ratio,
                    metrics={"observed_value": ratio, "threshold": self.threshold},
                    description=(
                        f"{column} violates expected {self.target_semantic} "
                        f"pattern (match ratio: {ratio:.2%})"
                    ),
                )
            ]
        return []
