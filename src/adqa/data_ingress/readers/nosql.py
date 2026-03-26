# adqa/data_ingress/readers/nosql.py
from typing import Any, override

import pandas as pd

from ..reader import DataReader


class NoSQLReader(DataReader):
    def __init__(self, uri: str, collection: str, query: dict[str, Any] | None = None):
        self.uri: str = uri
        self.collection: str = collection
        self.query: dict[str, Any] = query or {}

    @override
    def read(self) -> pd.DataFrame:
        try:
            from pymongo import MongoClient
        except ImportError as err:
            raise ImportError(
                "pymongo is not installed."
                + " Install it with `pip install adqa[mongo]`"
            ) from err

        client: MongoClient[Any] = MongoClient(self.uri)
        db = client.get_default_database()
        cursor = db[self.collection].find(self.query)
        # Iterate over cursor directly
        return pd.DataFrame(cursor)

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "nosql",
            "uri": self.uri,
            "collection": self.collection,
            "query": self.query,
        }
