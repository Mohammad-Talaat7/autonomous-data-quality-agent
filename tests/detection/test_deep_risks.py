import pandas as pd

from adqa import ADQA, ADQAConfig


def test_deep_risk_data_drift():
    # 1. Create baseline
    df_base = pd.DataFrame({"val": [10, 10, 11, 10, 11, 10]})  # Mean ~10.3

    config = ADQAConfig(tracing_enabled=False)
    agent_base = ADQA.from_df(df_base, config=config)
    result_base = agent_base.analyze()

    # 2. Create drifty data
    df_drift = pd.DataFrame(
        {"val": [100, 100, 110, 100, 110, 100]}  # Mean shifted significantly
    )

    # 3. Run analysis with historical profile
    agent_drift = ADQA.from_df(
        df_drift, config=config, historical_profiles=result_base.profiles
    )
    result_drift = agent_drift.analyze()

    # 4. Verify drift detected
    drift_detections = [
        d for d in result_drift.detections.detections if d.issue_type == "data_drift"
    ]
    assert len(drift_detections) > 0
    assert "shifted" in drift_detections[0].description


def test_deep_risk_quasi_id():
    # Combination of ZIP, Gender, DOB that is unique for every row
    df = pd.DataFrame(
        {
            "zip_code": ["12345", "12346", "12347", "12348"],
            "gender": ["M", "F", "M", "F"],
            "birth_year": [1980, 1981, 1982, 1983],
            "other": [1, 1, 1, 1],
        }
    )

    config = ADQAConfig(tracing_enabled=False)
    agent = ADQA.from_df(df, config=config)
    result = agent.analyze()

    # Verify quasi-id risk detected
    qi_detections = [
        d
        for d in result.detections.detections
        if d.issue_type == "quasi_identifier_risk"
    ]
    assert len(qi_detections) > 0
    assert "re-identification risk" in qi_detections[0].description


def test_deep_risk_semantic_violation():
    df = pd.DataFrame(
        {
            "age": [25, 30, -5, 200],  # -5 and 200 are semantic violations
            "price": [10.5, -1.0, 5.0, 0.0],  # -1.0 is a semantic violation
        }
    )

    config = ADQAConfig(tracing_enabled=False)
    agent = ADQA.from_df(df, config=config)
    result = agent.analyze()

    # Verify semantic violations detected
    violation_detections = [
        d for d in result.detections.detections if d.issue_type == "semantic_violation"
    ]
    assert len(violation_detections) >= 2

    # Check columns
    violated_cols = {d.column for d in violation_detections}
    assert "age" in violated_cols
    assert "price" in violated_cols
