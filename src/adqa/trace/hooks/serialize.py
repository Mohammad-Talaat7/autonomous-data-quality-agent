# adqa/trace/hooks/serialize.py

from collections.abc import Mapping, Sequence
from typing import cast

from ..enums import TraceValue


def to_trace_value(v: object) -> TraceValue:
    """
    recursively converts an arbitrary object into a TraceValue.
    """
    if v is None or isinstance(v, str | int | float | bool):
        return v

    if isinstance(v, Sequence) and not isinstance(v, str | bytes):
        return [to_trace_value(x) for x in v]

    if isinstance(v, Mapping):
        return {
            str(k): to_trace_value(val)
            for k, val in cast(Mapping[object, object], v).items()
        }

    return repr(v)
