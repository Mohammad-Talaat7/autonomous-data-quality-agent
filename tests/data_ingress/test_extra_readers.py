from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from adqa.data_ingress.readers.airbyte import AirbyteReader
from adqa.data_ingress.readers.data_warehouses import WarehouseReader
from adqa.data_ingress.readers.database import DatabaseReader
from adqa.data_ingress.readers.nosql import NoSQLReader


def test_airbyte_reader_missing_dependency():
    with patch("adqa.data_ingress.readers.airbyte.ab", None):
        with pytest.raises(ImportError) as excinfo:
            AirbyteReader("source", {}, "stream")

        assert "PyAirbyte is not installed" in str(excinfo.value)
        import sys

        if sys.version_info >= (3, 13):
            assert "incompatible with Python 3.13+" in str(excinfo.value)


def test_nosql_reader_read():
    mock_mongo = MagicMock()
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_mongo.MongoClient.return_value = mock_client
    mock_client.get_default_database.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value = [{"a": 1}, {"a": 2}]

    with patch.dict("sys.modules", {"pymongo": mock_mongo}):
        reader = NoSQLReader(uri="mongodb://localhost", collection="test")
        df = reader.read()

        assert len(df) == 2
        assert df.iloc[0]["a"] == 1


@patch("sqlalchemy.create_engine")
@patch("pandas.read_sql")
def test_database_reader(mock_read_sql, mock_create_engine):
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    mock_read_sql.return_value = pd.DataFrame({"a": [1]})

    reader = DatabaseReader("sqlite:///:memory:", "SELECT * FROM table")
    df = reader.read()

    mock_create_engine.assert_called_with("sqlite:///:memory:")
    mock_read_sql.assert_called_with("SELECT * FROM table", mock_connection)
    assert not df.empty


@patch("sqlalchemy.create_engine")
@patch("pandas.read_sql")
def test_warehouse_reader(mock_read_sql, mock_create_engine):
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    mock_read_sql.return_value = pd.DataFrame({"a": [1]})

    reader = WarehouseReader("snowflake://...", "SELECT 1", "snowflake")
    reader.read()

    mock_create_engine.assert_called_with("snowflake://...")
    assert reader.describe()["type"] == "warehouse"
