# tests/data_ingress/test_readers.py

from unittest.mock import MagicMock, patch

import pandas as pd

from adqa.data_ingress.readers.csv import CSVReader
from adqa.data_ingress.readers.dataframe import DataFrameReader
from adqa.data_ingress.readers.excel import ExcelReader
from adqa.data_ingress.readers.parquet import ParquetReader
from adqa.data_ingress.readers.remote_file import RemoteFileReader


def test_csv_reader(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path, index=False)

    reader = CSVReader(str(csv_path))
    result_df = reader.read()

    pd.testing.assert_frame_equal(df, result_df)
    assert reader.describe()["type"] == "csv"


@patch("pandas.read_parquet")
def test_parquet_reader(mock_read_parquet):
    df = pd.DataFrame({"a": [1, 2]})
    mock_read_parquet.return_value = df

    reader = ParquetReader("test.parquet")
    result_df = reader.read()

    mock_read_parquet.assert_called_once_with("test.parquet")
    pd.testing.assert_frame_equal(df, result_df)
    assert reader.describe()["type"] == "parquet"


@patch("pandas.read_excel")
def test_excel_reader(mock_read_excel):
    df = pd.DataFrame({"a": [1, 2]})
    mock_read_excel.return_value = df

    reader = ExcelReader("test.xlsx", sheet_name="Sheet1")
    result_df = reader.read()

    mock_read_excel.assert_called_once_with("test.xlsx", sheet_name="Sheet1")
    pd.testing.assert_frame_equal(df, result_df)
    assert reader.describe()["type"] == "excel"


@patch("requests.get")
@patch("pandas.read_csv")
def test_remote_file_reader_csv(mock_read_csv, mock_get):
    mock_response = MagicMock()
    mock_response.content = b"csv,data"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    df = pd.DataFrame({"a": [1]})
    mock_read_csv.return_value = df

    reader = RemoteFileReader(url="http://example.com/data.csv", format="csv")
    result_df = reader.read()

    mock_get.assert_called_once()
    pd.testing.assert_frame_equal(df, result_df)
    assert reader.describe()["format"] == "csv"


@patch("requests.get")
@patch("pandas.read_parquet")
def test_remote_file_reader_parquet(mock_read_parquet, mock_get):
    mock_response = MagicMock()
    mock_response.content = b"parquet_data"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    df = pd.DataFrame({"a": [1]})
    mock_read_parquet.return_value = df

    reader = RemoteFileReader(url="http://example.com/data.parquet", format="parquet")
    result_df = reader.read()

    pd.testing.assert_frame_equal(df, result_df)
    assert reader.describe()["format"] == "parquet"


@patch("requests.get")
@patch("pandas.read_excel")
def test_remote_file_reader_excel(mock_read_excel, mock_get):
    mock_response = MagicMock()
    mock_response.content = b"excel_data"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    df = pd.DataFrame({"a": [1]})
    mock_read_excel.return_value = df

    reader = RemoteFileReader(url="http://example.com/data.xlsx", format="excel")
    result_df = reader.read()

    pd.testing.assert_frame_equal(df, result_df)
    assert reader.describe()["format"] == "excel"


def test_dataframe_reader():
    df = pd.DataFrame({"a": [1, 2]})
    reader = DataFrameReader(df)
    result_df = reader.read()

    pd.testing.assert_frame_equal(df, result_df)
    assert reader.describe()["rows"] == 2
