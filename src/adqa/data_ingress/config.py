# adqa/data_ingress/config.py

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .types import DataSourceType


@dataclass(frozen=True)
class DataSourceConfig:
    type: DataSourceType
    params: Mapping[str, Any]
