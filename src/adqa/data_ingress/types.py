# adqa/data_ingress/types.py

from enum import Enum


class DataSourceType(Enum):
    CSV = "csv"
    PARQUET = "parquet"
    EXCEL = "excel"

    DATABASE = "database"  # SQL-like
    NOSQL = "nosql"  # document / key-value

    REMOTE_FILE = "remote_file"  # HTTP(S)
    S3 = "s3"  # object storage

    DATAFRAME = "dataframe"  # in-memory

    WAREHOUSE = "warehouse"  # BigQuery / Snowflake / etc
