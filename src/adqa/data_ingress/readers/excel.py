# adqa/data_ingress/readers/excel.py

from typing import Any, override

import pandas as pd

from ..reader import DataReader


class ExcelReader(DataReader):
    """
    Reads data from a local Excel file.
    """

    def __init__(self, path: str, sheet_name: str | int = 0):
        self.path: str = path
        self.sheet_name: str | int = sheet_name

    @override
    def read(self) -> pd.DataFrame:
        try:
            return pd.read_excel(self.path, sheet_name=self.sheet_name)
        except ImportError as err:
            raise ImportError(
                "openpyxl or xlrd is not installed."
                + " Install with `pip install adqa[excel]`"
            ) from err
        except Exception as e:
            raise RuntimeError(
                f"Failed to read Excel file from {self.path}: {e}"
            ) from e

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "excel",
            "path": self.path,
            "sheet_name": self.sheet_name,
        }
