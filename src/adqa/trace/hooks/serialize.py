# adqa/trace/hooks/serialize.py

from collections.abc import Mapping, Sequence
from typing import cast

from ..enums import TraceValue


def to_trace_value(
    v: object, max_seq_len: int = 50, max_str_len: int = 1000
) -> TraceValue:
    """
    recursively converts an arbitrary object into a TraceValue,
    with safety limits for collection size and string length.
    """
    if v is None:
        return None

    if isinstance(v, str):
        if len(v) > max_str_len:
            return v[:max_str_len] + "... (truncated)"
        return v

    if isinstance(v, int | float | bool):
        return v

    if hasattr(v, "to_dict"):
        # We don't recurse with the same limits here to allow the object's
        # to_dict to define its own structure, but we will catch its nested parts.
        return to_trace_value(v.to_dict(), max_seq_len, max_str_len)

    if isinstance(v, Sequence) and not isinstance(v, str | bytes):
        items = list(v)
        if len(items) > max_seq_len:
            truncated = [
                to_trace_value(x, max_seq_len, max_str_len) for x in items[:max_seq_len]
            ]
            truncated.append(f"... (truncated {len(items) - max_seq_len} more items)")
            return truncated
        return [to_trace_value(x, max_seq_len, max_str_len) for x in items]

    if isinstance(v, Mapping):
        return {
            str(k): to_trace_value(val, max_seq_len, max_str_len)
            for k, val in cast(Mapping[object, object], v).items()
        }

    s = repr(v)
    if len(s) > max_str_len:
        return s[:max_str_len] + "... (truncated)"
    return s
