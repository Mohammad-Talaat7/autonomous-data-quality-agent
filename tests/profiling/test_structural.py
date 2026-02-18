from __future__ import annotations

import pandas as pd
import pytest

from adqa.profiling.models.column_profile import LogicalType
from adqa.profiling.structural.column_profiler import profile_column


def test_profile_numeric_column():
    series = pd.Series([1.0, 2.0, 3.0, 100.0, None], name="test_numeric")
    profile = profile_column(series)

    assert profile.name == "test_numeric"
    assert profile.logical_type == LogicalType.NUMERIC
    assert profile.structural_metrics.null_ratio == 0.2
    assert profile.numeric_metrics is not None
    assert profile.numeric_metrics.mean == pytest.approx(26.5)
    assert profile.numeric_metrics.min == 1.0
    assert profile.numeric_metrics.max == 100.0


def test_profile_categorical_column():
    # 10 rows, 3 unique values -> ratio 0.3 < 0.5
    series = pd.Series(["A"] * 5 + ["B"] * 3 + ["C"] * 2 + [None], name="test_cat")
    profile = profile_column(series)

    assert profile.name == "test_cat"
    assert profile.logical_type == LogicalType.CATEGORICAL
    assert profile.categorical_metrics is not None
    assert profile.categorical_metrics.cardinality == 3
    assert profile.categorical_metrics.mode == "A"


def test_profile_text_column():
    # Many unique values to trigger TEXT logic
    series = pd.Series([f"val_{i}" for i in range(100)], name="test_text")
    profile = profile_column(series)

    assert profile.logical_type == LogicalType.TEXT
    assert profile.text_metrics is not None
    assert profile.text_metrics.avg_length > 0
