from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from adqa.data_ingress.readers.s3 import S3Reader


def test_s3_reader_csv():
    mock_s3_client = MagicMock()
    mock_body = MagicMock()
    mock_s3_client.get_object.return_value = {"Body": mock_body}

    # Patch boto3.client directly.
    # Since it's imported inside the method, we patch 'boto3.client'
    with patch("boto3.client") as mock_client_func:
        mock_client_func.return_value = mock_s3_client

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({"col": [1, 2]})

            reader = S3Reader(
                bucket="my-bucket", key="data.csv", format="csv", region="us-east-1"
            )
            df = reader.read()

            mock_client_func.assert_called_with("s3", region_name="us-east-1")
            mock_s3_client.get_object.assert_called_with(
                Bucket="my-bucket", Key="data.csv"
            )
            mock_read_csv.assert_called_once_with(mock_body)
            assert len(df) == 2


def test_s3_reader_parquet():
    mock_s3_client = MagicMock()
    mock_s3_client.get_object.return_value = {"Body": MagicMock()}

    with patch("boto3.client") as mock_client_func:
        mock_client_func.return_value = mock_s3_client
        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_read_parquet.return_value = pd.DataFrame({"col": [1, 2]})

            reader = S3Reader(bucket="b", key="k.parquet", format="parquet")
            reader.read()

            mock_read_parquet.assert_called_once()


def test_s3_reader_missing_boto3():
    # To test the ImportError, we need to make 'import boto3' fail.
    # We can do this by patching sys.modules
    with patch.dict("sys.modules", {"boto3": None}):
        reader = S3Reader("b", "k")
        with pytest.raises(ImportError, match="boto3 is not installed"):
            reader.read()
