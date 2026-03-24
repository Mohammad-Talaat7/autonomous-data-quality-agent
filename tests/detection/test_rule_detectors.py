from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest
from adqa.config.model import DetectionThresholds
from adqa.detection.context import DetectionContext
from adqa.detection.rule_detectors.constant import ConstantColumnDetector
from adqa.detection.rule_detectors.correlation import CorrelationDetector
from adqa.detection.rule_detectors.duplicate import DuplicateRowsDetector
from adqa.detection.rule_detectors.imbalance import ImbalanceDetector
from adqa.detection.rule_detectors.missing import MissingValuesDetector
from adqa.detection.rule_detectors.outlier import OutlierDetector
from adqa.detection.rule_detectors.pattern import PatternDetector
from adqa.detection.rule_detectors.range import RangeDetector
from adqa.detection.rule_detectors.rare_category import RareCategoryDetector
from adqa.detection.rule_detectors.skewness import SkewnessDetector
from adqa.detection.rule_detectors.type_mismatch import TypeMismatchDetector
from adqa.detection.rule_detectors.zero_value import ZeroValueDetector


@pytest.fixture
def thresholds():
    return DetectionThresholds()


@pytest.fixture
def mock_context():
    dataset_profile = MagicMock()
    column_profiles = {}
    return DetectionContext(
        dataset_profile=dataset_profile, column_profiles=column_profiles
    )


def test_missing_values_detector(mock_context, thresholds):
    detector = MissingValuesDetector(thresholds=thresholds)

    # Below threshold (0.2)
    col_ok = MagicMock()
    col_ok.null_ratio = 0.1
    mock_context.column_profiles["col_ok"] = col_ok

    # Above threshold
    col_bad = MagicMock()
    col_bad.null_ratio = 0.3
    mock_context.column_profiles["col_bad"] = col_bad

    results = detector.detect(mock_context)

    assert len(results) == 1
    assert results[0].column == "col_bad"
    assert results[0].issue_type == "missing_values"


def test_constant_column_detector(mock_context, thresholds):
    detector = ConstantColumnDetector(thresholds=thresholds)

    col_ok = MagicMock()
    col_ok.unique_count = 10
    mock_context.column_profiles["col_ok"] = col_ok

    col_constant = MagicMock()
    col_constant.unique_count = 1
    mock_context.column_profiles["col_constant"] = col_constant

    results = detector.detect(mock_context)

    assert len(results) == 1
    assert results[0].column == "col_constant"
    assert results[0].issue_type == "constant_column"


def test_duplicate_rows_detector(mock_context, thresholds):
    detector = DuplicateRowsDetector(thresholds=thresholds)

    mock_context.dataset_profile.duplicate_ratio = 0.2
    results = detector.detect(mock_context)
    assert len(results) == 1
    assert results[0].issue_type == "duplicate_rows"

    mock_context.dataset_profile.duplicate_ratio = 0.05
    results = detector.detect(mock_context)
    assert len(results) == 0


def test_skewness_detector(mock_context, thresholds):
    detector = SkewnessDetector(thresholds=thresholds)

    col_ok = MagicMock()
    col_ok.skewness = 0.5
    mock_context.column_profiles["col_ok"] = col_ok

    col_skewed = MagicMock()
    col_skewed.skewness = 2.5
    mock_context.column_profiles["col_skewed"] = col_skewed

    results = detector.detect(mock_context)

    assert len(results) == 1
    assert results[0].column == "col_skewed"
    assert results[0].issue_type == "skewed_distribution"


def test_imbalance_detector(mock_context, thresholds):
    detector = ImbalanceDetector(thresholds=thresholds)

    col_ok = MagicMock()
    col_ok.value_distribution = {"A": 0.5, "B": 0.5}
    mock_context.column_profiles["col_ok"] = col_ok

    col_imbalanced = MagicMock()
    col_imbalanced.value_distribution = {"A": 0.95, "B": 0.05}
    mock_context.column_profiles["col_imbalanced"] = col_imbalanced

    results = detector.detect(mock_context)

    assert len(results) == 1
    assert results[0].column == "col_imbalanced"
    assert results[0].issue_type == "imbalance"


def test_correlation_detector(mock_context, thresholds):
    detector = CorrelationDetector(thresholds=thresholds)

    matrix = {("A", "A"): 1.0, ("A", "B"): 0.95, ("B", "B"): 1.0}
    mock_context.correlation_matrix = matrix

    results = detector.detect(mock_context)

    assert len(results) == 1
    assert sorted(results[0].columns) == ["A", "B"]
    assert results[0].issue_type == "high_correlation"


def test_pattern_detector(mock_context, thresholds):
    detector = PatternDetector(thresholds=thresholds, pattern=r"^\d{3}$")

    df = pd.DataFrame(
        {
            "col_ok": ["123", "456", "789", "012"],
            "col_bad": ["123", "abc", "789", "xyz"],  # 50% match < 80% threshold
        }
    )
    mock_context.raw_data_sample = df
    mock_context.column_profiles = {"col_ok": MagicMock(), "col_bad": MagicMock()}

    results = detector.detect(mock_context)

    assert len(results) == 1
    assert results[0].column == "col_bad"
    assert results[0].issue_type == "pattern_violation"


def test_range_detector(mock_context):
    thresholds = DetectionThresholds(min_value=0, max_value=100)
    detector = RangeDetector(thresholds=thresholds)

    col_ok = MagicMock()
    col_ok.numeric_metrics.min = 10
    col_ok.numeric_metrics.max = 90
    mock_context.column_profiles["col_ok"] = col_ok

    col_bad_min = MagicMock()
    col_bad_min.numeric_metrics.min = -5
    col_bad_min.numeric_metrics.max = 50
    mock_context.column_profiles["col_bad_min"] = col_bad_min

    col_bad_max = MagicMock()
    col_bad_max.numeric_metrics.min = 50
    col_bad_max.numeric_metrics.max = 150
    mock_context.column_profiles["col_bad_max"] = col_bad_max

    results = detector.detect(mock_context)

    assert len(results) == 2


def test_outlier_detector(mock_context, thresholds):
    detector = OutlierDetector(thresholds=thresholds)

    col_bad = MagicMock()
    col_bad.behavioral_metrics.outlier_ratio = 0.1  # > 0.05
    mock_context.column_profiles["col_bad"] = col_bad

    results = detector.detect(mock_context)
    assert len(results) == 1
    assert results[0].issue_type == "outlier_detection"


def test_zero_value_detector(mock_context, thresholds):
    detector = ZeroValueDetector(thresholds=thresholds)

    col_bad = MagicMock()
    col_bad.numeric_metrics.zero_ratio = 0.5  # > 0.3
    mock_context.column_profiles["col_bad"] = col_bad

    results = detector.detect(mock_context)
    assert len(results) == 1
    assert results[0].issue_type == "excessive_zeros"


def test_rare_category_detector(mock_context, thresholds):
    detector = RareCategoryDetector(thresholds=thresholds)

    col_bad = MagicMock()
    col_bad.value_distribution = {"A": 0.995, "B": 0.005}  # B is rare < 0.01
    mock_context.column_profiles["col_bad"] = col_bad

    results = detector.detect(mock_context)
    assert len(results) == 1
    assert results[0].issue_type == "rare_categories"


def test_type_mismatch_detector(mock_context):
    detector = TypeMismatchDetector()

    col_bad = MagicMock()
    col_bad.dtype = "int64"
    col_bad.logical_type = "categorical"  # Mismatch
    mock_context.column_profiles["col_bad"] = col_bad

    results = detector.detect(mock_context)
    assert len(results) == 1
    assert results[0].issue_type == "type_mismatch"
