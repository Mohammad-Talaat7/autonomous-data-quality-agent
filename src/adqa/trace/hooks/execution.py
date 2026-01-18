from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import TypedDict
from uuid import UUID

from ..emitter import TraceEmitter
from ..enums import TraceComponent, TraceEventType, TraceSeverity, TraceValue
from ..events import TraceEvent
from .context import (
    get_current_emitter,
    get_current_event_id,
    reset_current_emitter,
    reset_current_event_id,
    set_current_emitter,
    set_current_event_id,
)


class ExecutionContext(TypedDict):
    event_id: UUID
    outputs: dict[str, TraceValue] | None


@contextmanager
def execution_hook(
    *,
    name: str,
    component: TraceComponent,
    event_type: TraceEventType,
    emitter: TraceEmitter | None,
    inputs: dict[str, TraceValue] | None = None,
) -> Iterator[ExecutionContext | None]:
    if emitter is None:
        emitter = get_current_emitter()

    if emitter is None:
        yield None
        return

    emitter_token = set_current_emitter(emitter)

    try:
        parent_event_id = get_current_event_id()

        start_event = TraceEvent(
            trace_id=emitter.context.trace_id,
            parent_event_id=parent_event_id,
            component=component,
            event_type=event_type,
            severity=TraceSeverity.INFO,
            name=name,
            inputs=inputs or {},
        )

        emitter.emit(start_event)

        token = set_current_event_id(start_event.event_id)

        ctx: ExecutionContext = {
            "event_id": start_event.event_id,
            "outputs": None,
        }

        try:
            yield ctx

            emitter.emit(
                TraceEvent(
                    trace_id=start_event.trace_id,
                    parent_event_id=start_event.event_id,
                    component=component,
                    event_type=event_type,
                    severity=TraceSeverity.INFO,
                    name=f"{name}.success",
                    outputs=ctx["outputs"] or {},
                )
            )

        except Exception as exc:
            emitter.emit(
                TraceEvent(
                    trace_id=start_event.trace_id,
                    parent_event_id=start_event.event_id,
                    component=component,
                    event_type=event_type,
                    severity=TraceSeverity.ERROR,
                    name=f"{name}.failure",
                    outputs={"exception": repr(exc)},
                )
            )
            raise

        finally:
            reset_current_event_id(token)

    finally:
        reset_current_emitter(emitter_token)


@asynccontextmanager
async def async_execution_hook(
    *,
    name: str,
    component: TraceComponent,
    event_type: TraceEventType,
    emitter: TraceEmitter | None,
    inputs: dict[str, TraceValue] | None = None,
) -> AsyncIterator[ExecutionContext | None]:
    if emitter is None:
        emitter = get_current_emitter()

    if emitter is None:
        yield None
        return

    emitter_token = set_current_emitter(emitter)

    try:
        parent_event_id = get_current_event_id()

        start_event = TraceEvent(
            trace_id=emitter.context.trace_id,
            parent_event_id=parent_event_id,
            component=component,
            event_type=event_type,
            severity=TraceSeverity.INFO,
            name=name,
            inputs=inputs or {},
        )

        emitter.emit(start_event)
        token = set_current_event_id(start_event.event_id)

        ctx: ExecutionContext = {
            "event_id": start_event.event_id,
            "outputs": None,
        }

        try:
            yield ctx

            emitter.emit(
                TraceEvent(
                    trace_id=start_event.trace_id,
                    parent_event_id=start_event.event_id,
                    component=component,
                    event_type=event_type,
                    severity=TraceSeverity.INFO,
                    name=f"{name}.success",
                    outputs=ctx["outputs"] or {},
                )
            )

        except Exception as exc:
            emitter.emit(
                TraceEvent(
                    trace_id=start_event.trace_id,
                    parent_event_id=start_event.event_id,
                    component=component,
                    event_type=event_type,
                    severity=TraceSeverity.ERROR,
                    name=f"{name}.failure",
                    outputs={"exception": repr(exc)},
                )
            )
            raise

        finally:
            reset_current_event_id(token)

    finally:
        reset_current_emitter(emitter_token)
