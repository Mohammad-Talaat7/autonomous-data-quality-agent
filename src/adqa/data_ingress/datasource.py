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
    JSONSourceConfig,
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
    | JSONSourceConfig
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
    def json(**kwargs: Any) -> "DataSource":
        return DataSource(JSONSourceConfig(**kwargs))

    @staticmethod
    def load(path: str, **kwargs: Any) -> "DataSource":
        """
        Smart-load a data source based on its path/extension.
        """
        # 1. Database / Warehouse URIs
        db_prefixes = (
            "postgresql://",
            "postgres://",
            "mysql://",
            "sqlite://",
            "oracle://",
            "mssql://",
            "duckdb://",
            "snowflake://",
            "bigquery://",
            "redshift://",
        )
        if path.startswith(db_prefixes):
            query = kwargs.pop("query", None)
            if not query:
                raise ValueError(
                    f"Database/Warehouse URI detected but no 'query' "
                    f"provided for: {path}"
                )

            # Warehouse specific (simplified)
            if path.startswith(("snowflake://", "bigquery://", "redshift://")):
                w_type = path.split("://")[0]
                return DataSource.warehouse(
                    connection_url=path, query=query, warehouse_type=w_type, **kwargs
                )

            return DataSource.database(connection_url=path, query=query, **kwargs)

        # 2. Remote Files
        if path.startswith(("http://", "https://")):
            # Try to guess format from extension
            ext = path.split(".")[-1].lower()
            return DataSource(RemoteFileSourceConfig(url=path, format=ext, **kwargs))

        if path.startswith("s3://"):
            parts = path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            fmt = key.split(".")[-1].lower() if "." in key else "parquet"
            return DataSource(
                S3SourceConfig(bucket=bucket, key=key, format=fmt, **kwargs)
            )

        ext = path.split(".")[-1].lower()
        if ext == "csv":
            return DataSource.csv(path=path, **kwargs)
        if ext in ("parquet", "pq"):
            return DataSource.parquet(path=path, **kwargs)
        if ext in ("xls", "xlsx"):
            return DataSource.excel(path=path, **kwargs)
        if ext == "json":
            return DataSource.json(path=path, **kwargs)
        if ext in ("db", "sqlite"):
            # Auto-convert local DB file to SQLite URI
            # We use 3 slashes for relative or 4 for absolute,
            # but sqlite:///{path} usually works well with absolute paths.
            url = f"sqlite:///{path}"
            query = kwargs.pop("query", "SELECT * FROM data LIMIT 1000")
            return DataSource.database(connection_url=url, query=query, **kwargs)

        raise ValueError(f"Could not auto-discover data source type for: {path}")

    @staticmethod
    def from_df(df: pd.DataFrame) -> "DataSource":
        return DataSource(DataFrameSourceConfig(dataframe=df))

    @staticmethod
    def warehouse(**kwargs: Any) -> "DataSource":
        return DataSource(WarehouseSourceConfig(**kwargs))

    @staticmethod
    def dataframe(df: pd.DataFrame) -> "DataSource":
        return DataSource(DataFrameSourceConfig(dataframe=df))

    @staticmethod
    def remote_file(**kwargs: Any) -> "DataSource":
        return DataSource(RemoteFileSourceConfig(**kwargs))

    @staticmethod
    def database(**kwargs: Any) -> "DataSource":
        return DataSource(DatabaseSourceConfig(**kwargs))

    @staticmethod
    def s3(**kwargs: Any) -> "DataSource":
        return DataSource(S3SourceConfig(**kwargs))

    @staticmethod
    def nosql(**kwargs: Any) -> "DataSource":
        return DataSource(NoSQLSourceConfig(**kwargs))

    @staticmethod
    def airbyte(**kwargs: Any) -> "DataSource":
        return DataSource(AirbyteSourceConfig(**kwargs))
