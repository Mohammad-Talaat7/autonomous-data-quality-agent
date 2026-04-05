import pandas as pd
import pytest

from adqa.config import ADQAConfig, ExecutionMode
from adqa.core.api import ADQA
from adqa.data_ingress.datasource import DataSource


@pytest.fixture
def csv_data_source(tmp_path):
    df = pd.DataFrame(
        {"a": [1, 2, 3, None], "b": ["x", "y", "z", "x"], "c": [10.5, 11.2, 12.1, 10.5]}
    )
    path = tmp_path / "test.csv"
    df.to_csv(path, index=False)
    return DataSource.csv(path=str(path))


def test_full_pipeline_advisory(csv_data_source):
    config = ADQAConfig(execution_mode=ExecutionMode.ADVISORY, tracing_enabled=True)
    adqa = ADQA(data_source=csv_data_source, config=config)
    result = adqa.analyze()

    assert result.dataframe is not None
    assert result.profiles is not None
    assert result.detections is not None
    assert result.scores is not None
    assert result.decision is not None
    assert result.execution_mode == "advisory"
    assert not result.blocked
    assert result.trace_id is not None
    assert result.config_hash is not None
    assert result.error is None


def test_full_pipeline_automatic_block(tmp_path):
    df = pd.DataFrame(
        {
            "a": [None, None, None, 1],  # 75% missing
            "b": [1, 2, 3, 4],
        }
    )
    path = tmp_path / "fail.csv"
    df.to_csv(path, index=False)

    source = DataSource.csv(path=str(path))
    config = ADQAConfig(
        execution_mode=ExecutionMode.AUTOMATIC,
        tracing_enabled=True,
        detection={"thresholds": {"missing_values_threshold": 0.1}},  # Force FAIL
    )

    adqa = ADQA(data_source=source, config=config)
    result = adqa.analyze()

    assert result.decision.decision == "FAIL"
    assert result.blocked
    assert any(a.action_type == "BLOCK" for a in result.actions)


def test_full_pipeline_human_in_loop(tmp_path):
    df = pd.DataFrame({"a": [None, None, None, 1], "b": [1, 2, 3, 4]})
    path = tmp_path / "hil.csv"
    df.to_csv(path, index=False)

    source = DataSource.csv(path=str(path))
    config = ADQAConfig(
        execution_mode=ExecutionMode.HUMAN_IN_LOOP,
        tracing_enabled=True,
        detection={"thresholds": {"missing_values_threshold": 0.1}},
    )

    adqa = ADQA(data_source=source, config=config)
    result = adqa.analyze()

    assert result.decision.decision == "FAIL"
    assert not result.blocked
    assert len(result.actions) == 0
