# adqa/data_ingress/readers/remote_file.py

from io import BytesIO
from typing import Any, override

import pandas as pd

from ..reader import DataReader


class RemoteFileReader(DataReader):
    """
    Reads tabular data from an HTTP(S) endpoint.
    Supported formats: csv, parquet, excel
    """

    def __init__(
        self,
        url: str,
        format: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
    ):
        self.url: str = url
        self.format: str = format.lower()
        self.headers: dict[str, Any] = headers or {}
        self.timeout: int = timeout

    @override
    def read(self) -> pd.DataFrame:
        try:
            import requests
        except ImportError as err:
            raise ImportError(
                "requests is not installed. Install it with `pip install adqa[remote]`"
            ) from err

        response = requests.get(
            self.url,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

        content = BytesIO(response.content)

        if self.format == "csv":
            return pd.read_csv(content)

        if self.format == "parquet":
            try:
                return pd.read_parquet(content)
            except ImportError as err:
                raise ImportError(
                    "pyarrow is not installed."
                    + " Install it with `pip install adqa[databases]`"
                ) from err

        if self.format in ("xls", "xlsx", "excel"):
            try:
                return pd.read_excel(content)
            except ImportError as err:
                raise ImportError(
                    "openpyxl or xlrd is not installed."
                    + " Install with `pip install adqa[excel]`"
                ) from err

        raise ValueError(f"Unsupported remote file format: {self.format}")

    def describe(self) -> dict[str, Any]:
        return {
            "type": "remote_file",
            "url": self.url,
            "format": self.format,
        }
