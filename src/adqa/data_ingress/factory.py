# adqa/data_ingress/factory.py

from .configs import (
    AirbyteSourceConfig,
    CSVSourceConfig,
    DatabaseSourceConfig,
    DataFrameSourceConfig,
    ExcelSourceConfig,
    NoSQLSourceConfig,
    ParquetSourceConfig,
    RemoteFileSourceConfig,
    S3SourceConfig,
    WarehouseSourceConfig,
)
from .datasource import DataSource
from .reader import DataReader
from .readers.airbyte import AirbyteReader
from .readers.csv import CSVReader
from .readers.data_warehouses import WarehouseReader
from .readers.database import DatabaseReader
from .readers.dataframe import DataFrameReader
from .readers.excel import ExcelReader
from .readers.nosql import NoSQLReader
from .readers.parquet import ParquetReader
from .readers.remote_file import RemoteFileReader
from .readers.s3 import S3Reader


class DataReaderFactory:
    @staticmethod
    def create(source: DataSource) -> DataReader:
        cfg = source.config

        match cfg:
            case CSVSourceConfig():
                return CSVReader(cfg.path, cfg.delimiter, cfg.encoding)

            case ParquetSourceConfig():
                return ParquetReader(cfg.path)

            case ExcelSourceConfig():
                return ExcelReader(cfg.path, cfg.sheet_name)

            case DatabaseSourceConfig():
                return DatabaseReader(cfg.connection_url, cfg.query)

            case NoSQLSourceConfig():
                return NoSQLReader(cfg.uri, cfg.collection, cfg.query)

            case S3SourceConfig():
                return S3Reader(cfg.bucket, cfg.key, cfg.format, cfg.region)

            case RemoteFileSourceConfig():
                return RemoteFileReader(cfg.url, cfg.format)

            case DataFrameSourceConfig():
                return DataFrameReader(cfg.dataframe)

            case WarehouseSourceConfig():
                return WarehouseReader(
                    cfg.connection_url,
                    cfg.query,
                    cfg.warehouse_type,
                )

            case AirbyteSourceConfig():
                return AirbyteReader(
                    cfg.source_name,
                    cfg.config,
                    cfg.stream,
                )

            case _:
                raise NotImplementedError(
                    f"Unsupported data source config: {type(cfg)}"
                )
