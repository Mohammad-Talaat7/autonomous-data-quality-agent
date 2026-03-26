# adqa/trace/hooks/lineage_context.py

from contextvars import ContextVar, Token

from ..lineage.recorder import LineageRecorder

_current_lineage_recorder: ContextVar[LineageRecorder | None] = ContextVar(
    "trace_current_lineage_recorder",
    default=None,
)


def get_current_lineage_recorder() -> LineageRecorder | None:
    return _current_lineage_recorder.get()


def set_current_lineage_recorder(
    recorder: LineageRecorder | None,
) -> Token[LineageRecorder | None]:
    return _current_lineage_recorder.set(recorder)


def reset_current_lineage_recorder(token: Token[LineageRecorder | None]) -> None:
    _current_lineage_recorder.reset(token)
