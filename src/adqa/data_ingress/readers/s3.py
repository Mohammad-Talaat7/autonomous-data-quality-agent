# adqa/data_ingress/readers/s3.py
from typing import Any, override

import pandas as pd

from ..reader import DataReader


class S3Reader(DataReader):
    def __init__(
        self,
        bucket: str,
        key: str,
        format: str = "csv",
        region: str | None = None,
    ):
        self.bucket: str = bucket
        self.key: str = key
        self.format: str = format.lower()
        self.region: str | None = region

    @override
    def read(self) -> pd.DataFrame:
        try:
            import boto3
        except ImportError as err:
            raise ImportError(
                "boto3 is not installed. Install it with `pip install adqa[aws]`"
            ) from err

        s3 = boto3.client("s3", region_name=self.region)
        obj = s3.get_object(Bucket=self.bucket, Key=self.key)
        content = obj["Body"]

        if self.format == "csv":
            return pd.read_csv(content)
        elif self.format == "parquet":
            try:
                return pd.read_parquet(content)
            except ImportError as err:
                raise ImportError(
                    "pyarrow is not installed."
                    + " Install it with `pip install adqa[databases]`"
                ) from err
        elif self.format in ("xls", "xlsx", "excel"):
            try:
                return pd.read_excel(content)
            except ImportError as err:
                raise ImportError(
                    "openpyxl or xlrd is not installed."
                    + " Install with `pip install adqa[excel]`"
                ) from err
        else:
            raise ValueError(f"Unsupported S3 file format: {self.format}")

    @override
    def describe(self) -> dict[str, Any]:
        return {
            "type": "s3",
            "bucket": self.bucket,
            "key": self.key,
            "format": self.format,
            "region": self.region,
        }
