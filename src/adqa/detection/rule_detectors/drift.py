from ...config.model import DetectionThresholds
from ..base import ColumnDetector, DetectionContext, QualityDimension
from ..results import DetectionResult


class DriftDetector(ColumnDetector):
    """
    Detects data drift by comparing current column metrics with historical baselines.
    """

    name = "DriftDetector"
    dimension = QualityDimension.INTEGRITY

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        # Default drift threshold: 20% shift
        self.threshold = 0.2

    def detect_column(
        self, column: str, context: DetectionContext
    ) -> list[DetectionResult]:
        if not context.historical_profiles:
            return []

        current_profile = context.get_column(column)

        # historical_profiles is expected to be a dict of ColumnProfile or similar
        hist_profiles_map = {}
        if hasattr(context.historical_profiles, "dataset_profile"):
            hist_profiles_map = {
                p.name: p for p in context.historical_profiles.dataset_profile.columns
            }
        elif isinstance(context.historical_profiles, dict):
            hist_profiles_map = context.historical_profiles

        hist_profile = hist_profiles_map.get(column)
        if not hist_profile:
            return []

        results = []

        # 1. Numeric Drift (Mean Shift)
        if (
            hasattr(current_profile, "numeric_metrics")
            and current_profile.numeric_metrics
            and hasattr(hist_profile, "numeric_metrics")
            and hist_profile.numeric_metrics
        ):
            curr_mean = current_profile.numeric_metrics.mean
            hist_mean = hist_profile.numeric_metrics.mean

            if hist_mean != 0:
                shift = abs(curr_mean - hist_mean) / abs(hist_mean)
                if shift > self.threshold:
                    results.append(
                        DetectionResult(
                            detector_name=self.name,
                            issue_type="data_drift",
                            column=column,
                            severity_hint=min(shift, 1.0),
                            metrics={
                                "observed_shift": shift,
                                "threshold": self.threshold,
                                "metric": "mean",
                            },
                            description=(
                                f"{column} mean shifted by {shift:.2%} from "
                                "historical baseline"
                            ),
                        )
                    )

        # 2. Categorical Drift (Mode Ratio Shift)
        if (
            hasattr(current_profile, "categorical_metrics")
            and current_profile.categorical_metrics
            and hasattr(hist_profile, "categorical_metrics")
            and hist_profile.categorical_metrics
        ):
            curr_mode_ratio = current_profile.categorical_metrics.mode_ratio
            hist_mode_ratio = hist_profile.categorical_metrics.mode_ratio

            shift = abs(curr_mode_ratio - hist_mode_ratio)
            if shift > self.threshold:
                results.append(
                    DetectionResult(
                        detector_name=self.name,
                        issue_type="data_drift",
                        column=column,
                        severity_hint=min(shift, 1.0),
                        metrics={
                            "observed_shift": shift,
                            "threshold": self.threshold,
                            "metric": "mode_ratio",
                        },
                        description=(
                            f"{column} mode ratio shifted by {shift:.2%} "
                            "from historical baseline"
                        ),
                    )
                )

        return results
