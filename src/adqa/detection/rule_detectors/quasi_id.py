from ...config.model import DetectionThresholds
from ..base import BaseDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class QuasiIdentifierDetector(BaseDetector):
    """
    Detects combinations of columns that could lead to re-identification.
    Quasi-identifiers are pieces of information that are not of themselves unique
    identifiers, but can be combined with other data to uniquely identify an individual.
    """

    name = "QuasiIdentifierDetector"
    dimension = QualityDimension.PRIVACY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.threshold = 0.8  # Lowered from 0.95 for better detection

    def detect(self, context: DetectionContext) -> list[DetectionResult]:
        if context.raw_data_sample is None:
            return []

        df = context.raw_data_sample
        results = []

        # Identify potential quasi-identifiers based on logical types / semantic labels
        # Zip, DOB, Gender are the classic "quasi-identifier" trio.
        potential_qi_cols = []
        sensitive_keywords = {
            "zip",
            "postal",
            "birth",
            "gender",
            "sex",
            "age",
            "race",
            "ethnicity",
        }

        for col_name, _profile in context.column_profiles.items():
            is_qi = any(k in col_name.lower() for k in sensitive_keywords)

            # Also check semantic labels if available in ml_profiles
            if not is_qi and context.ml_profiles:
                for ml in context.ml_profiles:
                    if ml.target == col_name and ml.model_name == "semantic_classifier":
                        label = ml.outputs.get("predicted_class", "")
                        if label in sensitive_keywords:
                            is_qi = True
                            break

            if is_qi:
                potential_qi_cols.append(col_name)

        if len(potential_qi_cols) < 2:
            return []

        # Check combinations (limited to 3 columns for performance)
        from itertools import combinations

        for r in range(2, min(len(potential_qi_cols) + 1, 4)):
            for combo in combinations(potential_qi_cols, r):
                # Calculate uniqueness of the combination
                unique_combo_count = len(df[list(combo)].drop_duplicates())
                total_rows = len(df)

                if total_rows == 0:
                    continue

                uniqueness_ratio = unique_combo_count / total_rows

                if uniqueness_ratio > self.threshold:
                    results.append(
                        DetectionResult(
                            detector_name=self.name,
                            issue_type="quasi_identifier_risk",
                            column=None,  # Cross-column issue
                            columns=list(combo),
                            severity_hint=uniqueness_ratio,
                            metrics={
                                "uniqueness_ratio": uniqueness_ratio,
                                "threshold": self.threshold,
                            },
                            description=(
                                f"Combination of {combo} has high uniqueness "
                                f"({uniqueness_ratio:.2%}), posing a "
                                "re-identification risk."
                            ),
                        )
                    )

        return results
