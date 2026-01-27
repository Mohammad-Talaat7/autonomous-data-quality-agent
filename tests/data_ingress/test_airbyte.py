import pytest
# Disable if needed, as it takes some time to test.
# pytest.skip("Disabled", allow_module_level=True)

import pandas as pd
from adqa.data_ingress.airbyte import ab

from pathlib import Path

csv_path = Path(__file__).parent / "Orders.csv"


def test_source_faker():
    source = ab.get_source(
        "source-faker",
        config={"count": 50},
        docker_image=True,
        install_if_missing=True,
    )
    source.check()


def test_source_faker_read():
    source = ab.get_source(
        "source-faker",
        config={"count": 50},
        docker_image=True,
        install_if_missing=True,
    )
    source.check()
    source.select_all_streams()
    result = source.read()
    assert isinstance(result, dict)
    for df in result.values():
        assert isinstance(df, pd.DataFrame)


def test_source_local():
    source = ab.get_source(
        "source-file",
        config={
            "dataset_name": "Orders",
            "provider": {
                "storage": "local",
            },
            "url": str(csv_path),
            "format": "csv",
        },
        # use_python="3.11",
        docker_image=True,
        install_if_missing=True
    )
    source.check()


def test_source_local_read():
    source = ab.get_source(
        "source-file",
        config={
            "dataset_name": "Orders",
            "provider": {
                "storage": "local",
            },
            "url": str(csv_path),
            "format": "csv",
        },
        use_python="3.11",
        install_if_missing=True
    )
    source.check()
    source.select_all_streams()
    result = source.read()
    assert isinstance(result, dict)
    for df in result.values():
        assert isinstance(df, pd.DataFrame)
        # Check that AirByte-added columns are dropped (should have 12 columns)
        assert len(df.columns) == 12
