# adqa/data_ingress/readers/json.py

from typing import Any, override

import pandas as pd

from ..reader import DataReader


class JSONReader(DataReader):
    """
    Reads data from a local JSON file.
    """

    def __init__(self, path: str, orient: str = "records"):
        self.path: str = path
        self.orient: str = orient

    @override
    def read(self) -> pd.DataFrame:
        try:
            df = pd.read_json(self.path, orient="records")
            if not isinstance(df, pd.DataFrame):
                raise ValueError("Expected DataFrame from read_json")
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to read JSON file from {self.path}: {e}") from e

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "json",
            "path": self.path,
            "orient": self.orient,
        }
