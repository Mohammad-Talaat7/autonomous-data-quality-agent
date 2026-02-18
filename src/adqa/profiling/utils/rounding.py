from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from typing import Any


def round_value(value: Any, precision: int) -> Any:
    if isinstance(value, float):
        return round(value, precision)

    if isinstance(value, dict):
        return {k: round_value(v, precision) for k, v in value.items()}

    if isinstance(value, list | tuple):
        return type(value)(round_value(v, precision) for v in value)

    if is_dataclass(value) and not isinstance(value, type):
        kwargs = {}
        for f in fields(value):
            field_value = getattr(value, f.name)
            kwargs[f.name] = round_value(field_value, precision)
        return replace(value, **kwargs)

    return value
