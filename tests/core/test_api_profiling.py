from __future__ import annotations

import pandas as pd

from adqa.config.model import ADQAConfig
from adqa.core.api import ADQA
from adqa.data_ingress.datasource import DataSource


def test_adqa_analyze_with_profiling():
    df = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": ["X"] * 5,  # Categorical
            "C": [1.1, 2.2, 3.3, 4.4, 5.5],
        }
    )

    config = ADQAConfig(data_source=DataSource.dataframe(df), tracing_enabled=False)

    agent = ADQA(config=config)
    result = agent.analyze()

    assert result.dataframe is not None
    assert result.profiles is not None
    assert len(result.profiles.dataset_profile.columns) == 3

    # Check if we got column A profile
    col_a = next(c for c in result.profiles.dataset_profile.columns if c.name == "A")
    assert col_a.numeric_metrics is not None
    assert col_a.numeric_metrics.mean == 3.0
