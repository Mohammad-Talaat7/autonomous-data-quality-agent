# adqa/data_ingress/readers/airbyte.py
from typing import Any

import pandas as pd

from ..reader import DataReader

try:
    import airbyte as ab
except ImportError:
    ab = None


class AirbyteReader(DataReader):
    def __init__(self, source_name: str, config: dict[str, Any], stream: str):
        if ab is None:
            import sys
            msg = "PyAirbyte is not installed. Install it with `pip install adqa[airbyte]`."
            if sys.version_info >= (3, 13):
                msg += " Note: PyAirbyte is currently incompatible with Python 3.13+."
            raise ImportError(msg)

        self.source_name: str = source_name
        self.config: dict[str, Any] = config
        self.stream: str = stream

    def read(self) -> pd.DataFrame:
        source = ab.get_source(self.source_name)
        result = source.read(
            config=self.config,
            streams=[self.stream],
        )

        # Airbyte returns an iterable of records
        return pd.DataFrame(result[self.stream])
