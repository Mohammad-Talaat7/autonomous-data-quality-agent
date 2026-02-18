from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pandas as pd
import pytest

from adqa.config.model import ADQAConfig, ProfilingConfig
from adqa.data_ingress.datasource import DataSource
mock_sklearn = MagicMock()
sys.modules["sklearn"] = mock_sklearn
sys.modules["sklearn.ensemble"] = mock_sklearn

from adqa.profiling.engine import ProfilingEngine


@pytest.fixture
def mock_config():
    # Simple mock for DataSource as it's a protocol/base class
    ds = MagicMock(spec=DataSource)
    return ADQAConfig(
        data_source=ds,
        profiling=ProfilingConfig(
            sampling_threshold=100, sample_size=50, max_workers=2
        ),
    )


def test_profiling_engine_sampling(mock_config):
    # Create DF larger than threshold
    df = pd.DataFrame({"A": range(200), "B": range(200)})

    engine = ProfilingEngine(config=mock_config)
    result = engine.run(df)

    # Metadata should still show full row count
    assert result.dataset_profile.metadata.row_count == 200
    # Signals and profiles should have been generated
    assert len(result.dataset_profile.columns) == 2


def test_profiling_engine_parallel(mock_config):
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})

    engine = ProfilingEngine(config=mock_config)
    result = engine.run(df)

    assert len(result.dataset_profile.columns) == 3
    column_names = [c.name for c in result.dataset_profile.columns]
    assert sorted(column_names) == ["A", "B", "C"]
