# adqa/trace/hooks/context.py

from contextvars import ContextVar, Token
from uuid import UUID

from ..emitter import TraceEmitter

_current_event_id: ContextVar[UUID | None] = ContextVar(
    "trace_current_event_id",
    default=None,
)

_current_emitter: ContextVar[TraceEmitter | None] = ContextVar(
    "trace_current_emitter",
    default=None,
)


def get_current_event_id() -> UUID | None:
    return _current_event_id.get()


def set_current_event_id(event_id: UUID | None) -> Token[UUID | None]:
    return _current_event_id.set(event_id)


def reset_current_event_id(token: Token[UUID | None]) -> None:
    _current_event_id.reset(token)


def get_current_emitter() -> TraceEmitter | None:
    return _current_emitter.get()


def set_current_emitter(emitter: TraceEmitter | None) -> Token[TraceEmitter | None]:
    return _current_emitter.set(emitter)


def reset_current_emitter(token: Token[TraceEmitter | None]) -> None:
    _current_emitter.reset(token)
