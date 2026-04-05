# adqa/trace/hooks/decorators.py

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from ..emitter import TraceEmitter
from ..enums import TraceComponent, TraceEventType, TraceValue
from ..lineage.context_bridge import lineage_hook
from ..lineage.recorder import LineageRecorder
from .execution import execution_hook
from .serialize import to_trace_value

P = ParamSpec("P")
R = TypeVar("R")


def trace_metric(
    *, emitter: TraceEmitter | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with execution_hook(
                name=f"metric.{fn.__name__}",
                component=TraceComponent.METRIC,
                event_type=TraceEventType.EXECUTION,
                emitter=emitter,
                inputs={
                    "args": to_trace_value(args),
                    "kwargs": to_trace_value(kwargs),
                },
            ) as ctx:
                result = fn(*args, **kwargs)
                if ctx is not None:
                    ctx["outputs"] = {"result": to_trace_value(result)}
                return result

        return wrapper

    return decorator


def trace_rule(
    *, emitter: TraceEmitter | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with execution_hook(
                name=f"rule.{fn.__name__}",
                component=TraceComponent.RULE,
                event_type=TraceEventType.CHECK,
                emitter=emitter,
                inputs={
                    "args": to_trace_value(args),
                    "kwargs": to_trace_value(kwargs),
                },
            ) as ctx:
                result = fn(*args, **kwargs)
                if ctx is not None:
                    ctx["outputs"] = {"result": to_trace_value(result)}
                return result

        return wrapper

    return decorator


def trace_fix(
    *, emitter: TraceEmitter | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with execution_hook(
                name=f"fix.{fn.__name__}",
                component=TraceComponent.FIX,
                event_type=TraceEventType.PROPOSAL,
                emitter=emitter,
                inputs={
                    "args": to_trace_value(args),
                    "kwargs": to_trace_value(kwargs),
                },
            ) as ctx:
                result = fn(*args, **kwargs)
                if ctx is not None:
                    ctx["outputs"] = {"result": to_trace_value(result)}
                return result

        return wrapper

    return decorator


def trace_lineage(
    *,
    emitter: TraceEmitter | None = None,
    lineage: LineageRecorder | None = None,
    operation: str | None = None,
    metadata: dict[str, TraceValue] | None = None,
    capture_output: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            op_name = operation or fn.__name__
            with lineage_hook(
                lineage=lineage,
                emitter=emitter,
                operation=op_name,
                inputs={
                    "args": to_trace_value(args),
                    "kwargs": to_trace_value(kwargs),
                },
                metadata=metadata,
            ) as ctx:
                result = fn(*args, **kwargs)
                if capture_output and ctx is not None:
                    ctx["outputs"] = to_trace_value(result)
                return result

        return wrapper

    return decorator
