from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class MLProfile:
    model_name: str
    model_version: str
    target: str  # column name or "dataset"
    outputs: Mapping[str, float | str]
