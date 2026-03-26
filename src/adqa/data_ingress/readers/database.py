# adqa/data_ingress/readers/database.py
from typing import Any, override

import pandas as pd

from ..reader import DataReader


class DatabaseReader(DataReader):
    def __init__(self, connection_url: str, query: str):
        self.url: str = connection_url
        self.query: str = query

    @override
    def read(self) -> pd.DataFrame:
        from sqlalchemy import create_engine

        engine = create_engine(self.url)
        with engine.connect() as conn:
            return pd.read_sql(self.query, conn)

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "database",
            "url": self.url,
            "query": self.query,
        }
