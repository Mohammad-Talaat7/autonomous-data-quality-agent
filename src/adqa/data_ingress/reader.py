# adqa/data_ingress/reader.py

from abc import ABC, abstractmethod

import pandas as pd


class DataReader(ABC):
    @abstractmethod
    def read(self) -> pd.DataFrame:
        """Read data and return a pandas DataFrame."""
        raise NotImplementedError

    def describe(self) -> dict:
        """
        Optional metadata for tracing & audit.
        Must be JSON-serializable.
        """
        return {}
