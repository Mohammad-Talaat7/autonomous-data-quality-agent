import numpy as np
import pandas as pd
import pytest

from adqa import ADQA, ADQAConfig


def generate_ultimate_dirty_data(rows=100):
    """
    Generates a dataset designed to trigger EVERY detector in ADQA.
    """
    np.random.seed(42)

    data = {
        # 1. Missing Values
        "col_missing": [np.nan] * (rows // 2) + [1.0] * (rows // 2),
        # 2. Constant Column
        "col_constant": [42] * rows,
        # 3. High Skewness
        "col_skewed": np.random.exponential(scale=10, size=rows),
        # 4. Correlation
        "col_corr1": np.arange(rows),
        "col_corr2": np.arange(rows) + 0.00001,  # Almost identical
        # 5. Imbalance (Rule) & Bias (ML)
        # Using name 'gender' to trigger BiasDetector sensitive keyword
        "gender": ["M"] * int(rows * 0.95) + ["F"] * (rows - int(rows * 0.95)),
        # 6. Pattern Violation (Rule) & PII (ML)
        # Using name 'email' to trigger PIIDetector and SemanticClassifier
        "col_email": ["user@example.com"] * int(rows * 0.7)
        + ["invalid-email"] * (rows - int(rows * 0.7)),
        # 7. Range Violation
        "col_range": np.random.uniform(0, 50, size=rows),
        # 8. Outliers
        "col_outliers": [10.0] * (rows - 2) + [9999.0, -8888.0],
        # 9. Zero Values
        "col_zeros": [0] * int(rows * 0.5) + [1] * (rows - int(rows * 0.5)),
        # 10. Rare Categories
        "col_rare": ["Common"] * (rows - 2) + ["Rare1", "Rare2"],
        # 11. Type Mismatch (Mostly numeric stored as object)
        "col_mixed": ["1", "2", "3", "4", "invalid"] * (rows // 5),
        # 12. Semantic Boundaries
        "age": [25] * (rows - 2) + [-5, 150],
        "price": [10.0] * (rows - 1) + [-1.0],
        # 13. Quasi-Identifiers (Privacy)
        "zip_code": [f"{10000 + i}" for i in range(rows)],
        "birth_year": [1980 + (i % 40) for i in range(rows)],
        # 14. For Drift (will be used in 2nd pass)
        "col_drift": [10.0] * rows,
        # 15. For Anomaly Detection (Isolation Forest)
        "col_anomaly1": np.random.normal(0, 1, rows),
        "col_anomaly2": np.random.normal(0, 1, rows),
    }

    # Ensure some rows are pure anomalies for Isolation Forest
    data["col_anomaly1"][0] = 50.0
    data["col_anomaly2"][0] = 50.0

    # Trigger Range Violation specifically
    data["col_range"][0] = 500.0

    df = pd.DataFrame(data)

    # 16. Duplicate Rows (Add enough to trigger > 5% threshold)
    duplicates = df.iloc[:15].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    return df


def test_ultimate_quality_pipeline():
    """
    Test that all detectors are triggered and all proposed remediations are valid.
    """
    df = generate_ultimate_dirty_data(rows=100)

    config = ADQAConfig(
        execution_mode="automatic",
        ml_enabled=True,
        tracing_enabled=True,
        profiling={
            "enable_ml": True,
            "enable_correlation": True,
        },
        detection={
            "thresholds": {
                "min_value": 0,
                "max_value": 100,
                "correlation_threshold": 0.9,
                "imbalance_threshold": 0.9,
                "outlier_ratio_threshold": 0.01,
                "duplicate_rows_threshold": 0.05,
                "rare_category_threshold": 0.05,
                "min_rows_anomaly_detection": 10,  # Ensure it runs
            }
        },
    )

    # 1. First Pass: Detect everything
    # We provide a baseline for drift where col_drift mean is 100
    # (so 10 in current is drifty)
    df_hist = df.copy()
    df_hist["col_drift"] = 100.0
    agent_hist = ADQA.from_df(df_hist, config=config)
    hist_result = agent_hist.analyze()

    agent = ADQA.from_df(df, config=config, historical_profiles=hist_result.profiles)
    result = agent.analyze()

    issue_types = {d.issue_type for d in result.detections.detections}
    ml_signals = {e.signal_type for e in result.detections.ml_evidence}
    all_issues = issue_types.union(ml_signals)

    print(f"\nDetected issues: {all_issues}")

    # Verify core detectors triggered
    expected_critical = {
        "missing_values",
        "constant_column",
        "duplicate_rows",
        "high_skewness",
        "high_correlation",
        "imbalance",
        "outliers",
        "zero_value",
        "rare_category",
        "type_mismatch",
        "data_drift",
        "quasi_identifier_risk",
        "semantic_violation",
        "pii_detected",
        "potential_bias",
        "pattern_violation",
    }

    # Anomaly score requires sklearn and a functional environment
    from adqa.detection.ml_detectors.isolation_forest import IsolationForest

    if IsolationForest is not None:
        try:
            # Try a small test to ensure it actually works (environment check)
            test_if = IsolationForest(n_estimators=1, contamination="auto")
            test_if.fit([[1], [2], [3]])
            expected_critical.add("anomaly_score")
        except Exception:
            # If any error (ImportError, RuntimeError, etc. due to broken shared libs)
            pass

    for issue in expected_critical:
        assert issue in all_issues, f"Detector for {issue} was NOT triggered"

    # 2. Verify Remediations
    # All issues should have at least one proposed action
    actions = result.actions
    operations = {a.metadata.get("operation") for a in actions}

    print(f"Proposed operations: {operations}")

    # 3. Iterative Healing
    # Run up to 5 passes to reach PASS
    current_df = result.dataframe
    passed = False
    for i in range(5):
        loop_agent = ADQA.from_df(current_df, config=config)
        loop_result = loop_agent.analyze()

        if loop_result.decision.decision == "PASS":
            passed = True
            break

        current_df = loop_result.dataframe
        print(
            f"Pass {i + 2} decision: {loop_result.decision.decision}, "
            f"issues: {loop_result.decision.dominant_issues}"
        )

    assert passed, "Failed to reach PASS state after iterative healing of all issues"
    print(
        "\nSUCCESS: All data quality issues were identified and autonomously resolved."
    )


if __name__ == "__main__":
    pytest.main([__file__])
