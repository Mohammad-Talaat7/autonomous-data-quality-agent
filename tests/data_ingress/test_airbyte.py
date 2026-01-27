import pytest
# pytest.skip("Disabled", allow_module_level=True) # Disable if needed, as it takes some time to test.


from adqa.data_ingress.airbyte import ab

from pathlib import Path

csv_path = Path(__file__).parent / "Orders.csv"

def test_source_faker():
    source = ab.get_source(
        "source-faker",
        config={"count": 50},
        install_if_missing=True,
    )
    source.check()

def test_source_local():
    source = ab.get_source(
        "source-file",
        config={
            "dataset_name": "Orders",
            "provider": {
                "storage": "local",
            },
            "url": str(csv_path),
            "format": "csv"
        },
        install_if_missing=True,
    )
    source.check()