from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MLProfile:
    model_name: str
    model_version: str
    target: str  # column name or "dataset"
    outputs: Mapping[str, float | str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "target": self.target,
            "outputs": dict(self.outputs),
        }
