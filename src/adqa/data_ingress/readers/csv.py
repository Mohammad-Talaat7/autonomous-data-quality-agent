# adqa/data_ingress/readers/csv.py
from typing import Any, override

import pandas as pd

from ..reader import DataReader


class CSVReader(DataReader):
    def __init__(self, path: str, delimiter: str = ",", encoding: str = "utf-8"):
        self.path: str = path
        self.delimiter: str = delimiter
        self.encoding: str = encoding

    @override
    def read(self) -> pd.DataFrame:
        return pd.read_csv(
            self.path,
            sep=self.delimiter,
            encoding=self.encoding,
        )

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "csv",
            "path": self.path,
            "delimiter": self.delimiter,
            "encoding": self.encoding,
        }
