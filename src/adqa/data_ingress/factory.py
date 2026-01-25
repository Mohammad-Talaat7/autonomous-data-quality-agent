# adqa/data_ingress/factory.py

from .config import DataSourceConfig
from .reader import DataReader
from .readers.csv import CSVReader
from .readers.database import DatabaseReader
from .readers.dataframe import DataFrameReader
from .readers.excel import ExcelReader
from .readers.nosql import NoSQLReader
from .readers.parquet import ParquetReader
from .readers.remote_file import RemoteFileReader
from .readers.s3 import S3Reader
from .types import DataSourceType


class DataReaderFactory:
    @staticmethod
    def create(source: DataSourceConfig) -> DataReader:
        if source.type == DataSourceType.CSV:
            return CSVReader(**source.params)

        if source.type == DataSourceType.PARQUET:
            return ParquetReader(**source.params)

        if source.type == DataSourceType.EXCEL:
            return ExcelReader(**source.params)

        if source.type == DataSourceType.DATABASE:
            return DatabaseReader(**source.params)

        if source.type == DataSourceType.NOSQL:
            return NoSQLReader(**source.params)

        if source.type == DataSourceType.REMOTE_FILE:
            return RemoteFileReader(**source.params)

        if source.type == DataSourceType.S3:
            return S3Reader(**source.params)

        if source.type == DataSourceType.DATAFRAME:
            return DataFrameReader(**source.params)

        if source.type == DataSourceType.WAREHOUSE:
            raise NotImplementedError(
                "Warehouse readers are supported but not implemented yet"
            )

        raise ValueError(f"Unsupported data source type: {source.type}")
