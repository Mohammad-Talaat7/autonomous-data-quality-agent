# tests/data_ingress/test_factory.py

from adqa.data_ingress.datasource import DataSource
from adqa.data_ingress.factory import DataReaderFactory
from adqa.data_ingress.readers.csv import CSVReader
from adqa.data_ingress.readers.database import DatabaseReader
from adqa.data_ingress.readers.excel import ExcelReader
from adqa.data_ingress.readers.parquet import ParquetReader
from adqa.data_ingress.readers.remote_file import RemoteFileReader
from adqa.data_ingress.readers.s3 import S3Reader


def test_factory_creates_csv_reader():
    ds = DataSource.csv(path="test.csv")
    reader = DataReaderFactory.create(ds)
    assert isinstance(reader, CSVReader)


def test_factory_creates_parquet_reader():
    ds = DataSource.parquet(path="test.parquet")
    reader = DataReaderFactory.create(ds)
    assert isinstance(reader, ParquetReader)


def test_factory_creates_excel_reader():
    ds = DataSource.excel(path="test.xlsx")
    reader = DataReaderFactory.create(ds)
    assert isinstance(reader, ExcelReader)


def test_factory_creates_remote_file_reader():
    ds = DataSource.remote_file(url="http://example.com/data.csv", format="csv")
    reader = DataReaderFactory.create(ds)
    assert isinstance(reader, RemoteFileReader)


def test_factory_creates_database_reader():
    ds = DataSource.database(connection_url="sqlite://", query="SELECT 1")
    reader = DataReaderFactory.create(ds)
    assert isinstance(reader, DatabaseReader)


def test_factory_creates_s3_reader():
    ds = DataSource.s3(bucket="b", key="k", format="parquet")
    reader = DataReaderFactory.create(ds)
    assert isinstance(reader, S3Reader)
    assert reader.format == "parquet"
