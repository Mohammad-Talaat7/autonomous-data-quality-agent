# adqa/data_ingress/configs.py

from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict

from .types import DataSourceType


class BaseSourceConfig(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    type: DataSourceType


class CSVSourceConfig(BaseSourceConfig):
    path: str
    type: Literal[DataSourceType.CSV] = DataSourceType.CSV
    delimiter: str = ","
    encoding: str = "utf-8"


class ParquetSourceConfig(BaseSourceConfig):
    path: str
    type: Literal[DataSourceType.PARQUET] = DataSourceType.PARQUET


class ExcelSourceConfig(BaseSourceConfig):
    path: str
    type: Literal[DataSourceType.EXCEL] = DataSourceType.EXCEL
    sheet_name: str | int = 0


class DatabaseSourceConfig(BaseSourceConfig):
    connection_url: str
    query: str
    type: Literal[DataSourceType.DATABASE] = DataSourceType.DATABASE


class NoSQLSourceConfig(BaseSourceConfig):
    uri: str
    collection: str
    query: dict[str, Any] | None = None
    type: Literal[DataSourceType.NOSQL] = DataSourceType.NOSQL


class S3SourceConfig(BaseSourceConfig):
    bucket: str
    key: str
    format: str = "csv"
    region: str | None = None
    type: Literal[DataSourceType.S3] = DataSourceType.S3


class RemoteFileSourceConfig(BaseSourceConfig):
    url: str
    format: str  # csv | parquet | excel
    type: Literal[DataSourceType.REMOTE_FILE] = DataSourceType.REMOTE_FILE


class DataFrameSourceConfig(BaseSourceConfig):
    dataframe: pd.DataFrame
    type: Literal[DataSourceType.DATAFRAME] = DataSourceType.DATAFRAME


class WarehouseSourceConfig(BaseSourceConfig):
    connection_url: str
    query: str
    warehouse_type: str
    type: Literal[DataSourceType.WAREHOUSE] = DataSourceType.WAREHOUSE


class AirbyteSourceConfig(BaseSourceConfig):
    source_name: str
    config: dict[str, Any]
    stream: str
    type: Literal[DataSourceType.AIRBYTE] = DataSourceType.AIRBYTE
