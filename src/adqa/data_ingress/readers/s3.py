# adqa/data_ingress/readers/s3.py
from typing import override

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
        except ImportError:
            raise ImportError(
                "boto3 is not installed. Install it with `pip install adqa[aws]`"
            )

        s3 = boto3.client("s3", region_name=self.region)
        obj = s3.get_object(Bucket=self.bucket, Key=self.key)
        content = obj["Body"]

        if self.format == "csv":
            return pd.read_csv(content)
        elif self.format == "parquet":
            try:
                return pd.read_parquet(content)
            except ImportError:
                raise ImportError(
                    "pyarrow is not installed. Install it with `pip install adqa[databases]`"
                )
        elif self.format in ("xls", "xlsx", "excel"):
            try:
                return pd.read_excel(content)
            except ImportError:
                raise ImportError(
                    "openpyxl or xlrd is not installed. Install with `pip install adqa[excel]`"
                )
        else:
            raise ValueError(f"Unsupported S3 file format: {self.format}")
