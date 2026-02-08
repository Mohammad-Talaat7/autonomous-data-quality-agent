# adqa/data_ingress/datasource.py
from dataclasses import dataclass
from typing import Any

import pandas as pd

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

InternalSourceConfig = (
    CSVSourceConfig
    | ParquetSourceConfig
    | ExcelSourceConfig
    | DatabaseSourceConfig
    | NoSQLSourceConfig
    | S3SourceConfig
    | RemoteFileSourceConfig
    | DataFrameSourceConfig
    | WarehouseSourceConfig
    | AirbyteSourceConfig
)


@dataclass(frozen=True)
class DataSource:
    config: InternalSourceConfig

    @staticmethod
    def csv(**kwargs: Any) -> "DataSource":
        return DataSource(CSVSourceConfig(**kwargs))

    @staticmethod
    def parquet(**kwargs: Any) -> "DataSource":
        return DataSource(ParquetSourceConfig(**kwargs))

    @staticmethod
    def excel(**kwargs: Any) -> "DataSource":
        return DataSource(ExcelSourceConfig(**kwargs))

    @staticmethod
    def database(**kwargs: Any) -> "DataSource":
        return DataSource(DatabaseSourceConfig(**kwargs))

    @staticmethod
    def nosql(**kwargs: Any) -> "DataSource":
        return DataSource(NoSQLSourceConfig(**kwargs))

    @staticmethod
    def s3(**kwargs: Any) -> "DataSource":
        return DataSource(S3SourceConfig(**kwargs))

    @staticmethod
    def remote_file(**kwargs: Any) -> "DataSource":
        return DataSource(RemoteFileSourceConfig(**kwargs))

    @staticmethod
    def dataframe(df: pd.DataFrame) -> "DataSource":
        return DataSource(DataFrameSourceConfig(dataframe=df))

    @staticmethod
    def warehouse(**kwargs: Any) -> "DataSource":
        return DataSource(WarehouseSourceConfig(**kwargs))

    @staticmethod
    def airbyte(**kwargs: Any) -> "DataSource":
        return DataSource(AirbyteSourceConfig(**kwargs))
