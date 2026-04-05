import pandas as pd
import pytest

from adqa import ADQA, ADQAConfig, DataSource


@pytest.fixture
def fail_data():
    # 'a' is 100% missing -> should be REMEDIATED (dropped)
    # 'b' is valid
    return pd.DataFrame({"a": [None, None, None], "b": [1, 2, 3]})


def test_autonomous_healing_automatic(fail_data, tmp_path):
    path = tmp_path / "healing.csv"
    fail_data.to_csv(path, index=False)

    source = DataSource.csv(path=str(path))
    # Using AUTOMATIC mode with 100% missing column
    config = ADQAConfig(
        execution_mode=ADQAConfig.Mode.AUTOMATIC,
        tracing_enabled=True,
        detection={"thresholds": {"missing_values_threshold": 0.1}},
    )

    agent = ADQA(data_source=source, config=config)
    result = agent.analyze()

    print(f"\nDebug Column Breakdown: {result.decision.column_breakdown}")
    print(f"Debug Dominant Issues: {result.decision.dominant_issues}")

    # Verify 'a' was dropped (missing values)
    assert "a" not in result.dataframe.columns
    # Verify 'b' remains (valid data)
    assert "b" in result.dataframe.columns
    assert len(result.dataframe.columns) == 1
    assert any(
        a.action_type in ("REMEDIATE", "DROP", "IMPUTE", "CLIP", "TRANSFORM", "REPAIR")
        for a in result.actions
    )
    print("\nVerified: Column 'a' was autonomously healed (dropped).")


def test_autonomous_healing_human_in_loop(fail_data, tmp_path):
    path = tmp_path / "hil_healing.csv"
    fail_data.to_csv(path, index=False)

    source = DataSource.csv(path=str(path))
    config = ADQAConfig(
        execution_mode=ADQAConfig.Mode.HUMAN_IN_LOOP,
        tracing_enabled=True,
        detection={"thresholds": {"missing_values_threshold": 0.1}},
    )

    agent = ADQA(data_source=source, config=config)
    result = agent.analyze()

    # In HIL, it should NOT be dropped yet
    assert "a" in result.dataframe.columns
    assert result.approval_payload is not None

    # Approve and resume
    plan = result.plan
    plan.approved = True

    # We pass the original df to resume
    final_result = agent.execute_plan(plan, df=result.dataframe)

    # NOW it should be dropped
    assert "a" not in final_result.dataframe.columns
    assert any(
        a.action_type in ("REMEDIATE", "DROP", "IMPUTE", "CLIP", "TRANSFORM", "REPAIR")
        for a in final_result.actions
    )
    print("\nVerified: Column 'a' was healed after human approval.")


def test_autonomous_healing_outliers_and_correlation(tmp_path):
    df = pd.DataFrame(
        {
            "col_outliers": [10, 12, 11, 13, 14, 9999],
            "col_corr1": [1, 2, 3, 4, 5, 6],
            "col_corr2": [1, 2, 3, 4, 5, 6],
        }
    )
    path = tmp_path / "persistent.csv"
    df.to_csv(path, index=False)

    source = DataSource.csv(path=str(path))
    config = ADQAConfig(
        execution_mode=ADQAConfig.Mode.AUTOMATIC,
        tracing_enabled=True,
        profiling={"enable_correlation": True},
        detection={
            "thresholds": {
                "outlier_ratio_threshold": 0.05,
                "correlation_threshold": 0.9,
                "skewness_threshold": 1.0,
            }
        },
    )

    agent = ADQA(data_source=source, config=config)

    # First pass: should remediate outliers (clip) and correlation (drop col1)
    result = agent.analyze()

    # Verify remediations happened
    assert ("col_corr1" not in result.dataframe.columns) or (
        "col_corr2" not in result.dataframe.columns
    )

    # It might take a second pass because clipping col_outliers
    # doesn't necessarily fix its skewness and might introduce new
    # correlations or keep existing ones above threshold.
    # Second pass: should reach PASS
    max_passes = 3
    current_df = result.dataframe
    for _i in range(max_passes):
        agent_loop = ADQA.from_df(current_df, config=config)
        result_loop = agent_loop.analyze()
        if result_loop.decision.decision in ("PASS", "WARN"):
            break
        current_df = result_loop.dataframe
    else:
        pytest.fail(
            f"Failed to reach PASS/WARN after {max_passes} passes. "
            f"Final decision: {result_loop.decision.decision}"
        )


def test_autonomous_healing_tiny_dataset_anomaly_skip(tmp_path):
    # Dataset with 5 rows < 20 default threshold
    df = pd.DataFrame(
        {
            "a": [
                1,
                2,
                3,
                4,
                1000,
            ],  # 1000 is an outlier but IsolationForest should skip
            "b": [1, 1, 1, 1, 1],
        }
    )

    config = ADQAConfig(
        execution_mode=ADQAConfig.Mode.AUTOMATIC, tracing_enabled=True, ml_enabled=True
    )

    agent = ADQA.from_df(df, config=config)
    result = agent.analyze()

    # IsolationForest should NOT have run/emitted evidence
    anomaly_actions = [a for a in result.actions if "anomalous" in a.reason]
    assert len(anomaly_actions) == 0


def test_autonomous_healing_imbalance_remediation(tmp_path):
    # col_imbalanced has 95% 'A'
    df = pd.DataFrame({"col_imbalanced": ["A"] * 19 + ["B"]})

    config = ADQAConfig(
        execution_mode=ADQAConfig.Mode.AUTOMATIC,
        tracing_enabled=True,
        detection={"thresholds": {"imbalance_threshold": 0.9}},
    )

    agent = ADQA.from_df(df, config=config)
    result = agent.analyze()

    # Should propose dropping col_imbalanced (since 0.95 > 0.9)
    assert any("Drop col_imbalanced" in a.reason for a in result.actions)
    assert "col_imbalanced" not in result.dataframe.columns
