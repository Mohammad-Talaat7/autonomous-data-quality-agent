# adqa/data_ingress/readers/parquet.py

from typing import Any, override

import pandas as pd

from ..reader import DataReader


class ParquetReader(DataReader):
    """
    Reads data from a local Parquet file.
    """

    def __init__(self, path: str):
        self.path: str = path

    @override
    def read(self) -> pd.DataFrame:
        try:
            return pd.read_parquet(self.path)
        except ImportError as err:
            raise ImportError(
                "pyarrow is not installed."
                + " Install it with `pip install adqa[databases]`"
            ) from err
        except Exception as e:
            raise RuntimeError(
                f"Failed to read Parquet file from {self.path}: {e}"
            ) from e

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "parquet",
            "path": self.path,
        }
