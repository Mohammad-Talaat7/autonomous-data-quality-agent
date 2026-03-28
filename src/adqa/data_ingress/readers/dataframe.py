# adqa/data_ingress/readers/dataframe.py
from typing import Any, override

import pandas as pd

from ..reader import DataReader


class DataFrameReader(DataReader):
    def __init__(self, dataframe: pd.DataFrame):
        self.df: pd.DataFrame = dataframe

    @override
    def read(self) -> pd.DataFrame:
        return self.df.copy()

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "dataframe",
            "rows": len(self.df),
            "columns": list(self.df.columns),
        }
