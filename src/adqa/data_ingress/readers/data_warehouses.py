# adqa/data_ingress/readers/warehouse.py

from typing import Any, override

import pandas as pd

from ..reader import DataReader


class WarehouseReader(DataReader):
    """
    Generic SQL-based data warehouse reader.
    Works with BigQuery, Snowflake, Redshift, etc
    via SQLAlchemy-compatible drivers.
    """

    def __init__(
        self,
        connection_url: str,
        query: str,
        warehouse_type: str,
    ):
        self.connection_url: str = connection_url
        self.query: str = query
        self.warehouse_type: str = warehouse_type

    @override
    def read(self) -> pd.DataFrame:
        from sqlalchemy import create_engine

        engine = create_engine(self.connection_url)
        with engine.connect() as conn:
            return pd.read_sql(self.query, conn)

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "warehouse",
            "warehouse_type": self.warehouse_type,
            "query_hash": hash(self.query),
        }
