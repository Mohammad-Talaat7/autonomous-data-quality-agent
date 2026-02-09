# adqa/api.py


from uuid import UUID

from adqa.trace.hooks.serialize import to_trace_value

from .config import ADQAConfig, ConfigSnapshot, TraceStoreType, snapshot_from_config
from .data_ingress.factory import DataReaderFactory
from .data_ingress.reader import DataReader
from .result import ADQAResult
from .trace.context import TraceContext
from .trace.emitter import TraceEmitter
from .trace.enums import TraceEventType
from .trace.events import TraceEvent
from .trace.lineage import LineageRecorder
from .trace.lineage.memory import InMemoryLineageAdapter
from .trace.noop import NoOpLineageRecorder, NoOpTraceEmitter
from .trace.store import InMemoryTraceStore, JSONTraceStore


class ADQA:
    """
    Public entry point for ADQA.
    Orchestrates the Phase 3 pipeline.
    """

    def __init__(self, *, config: ADQAConfig):
        self._config: ADQAConfig = config

        # Build reader early → fail fast
        self._reader: DataReader = DataReaderFactory.create(config.data_source)

        # Lineage setup
        self._lineage: NoOpLineageRecorder | LineageRecorder = self._init_lineage()

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def analyze(self) -> ADQAResult:
        """
        Run ADQA analysis.
        Phase 3: data ingress only (profiling/detection next).
        """
        trace_id, trace_emitter, snapshot = self._initialize_trace_session()

        # ---- Data ingress ----
        trace_emitter.emit(
            TraceEvent(
                trace_id=trace_id,
                event_type=TraceEventType.DATA_INGRESS,
                name="READ_DATA_START",
            )
        )

        try:
            df = self._reader.read()
        except Exception as e:
            trace_emitter.emit(
                TraceEvent(
                    trace_id=trace_id,
                    event_type=TraceEventType.ERROR,
                    name="READ_DATA_ERROR",
                    metadata={"error": str(e)},
                )
            )
            return ADQAResult(
                dataframe=None,
                execution_mode=self._config.execution_mode.value,
                trace_id=str(trace_id),
                config_hash=snapshot.hash(),
                error=str(e),
            )

        trace_emitter.emit(
            TraceEvent(
                trace_id=trace_id,
                event_type=TraceEventType.DATA_INGRESS,
                name="READ_DATA_END",
                metadata={
                    "rows": len(df),
                    "columns": list(df.columns),
                },
            )
        )

        # ---- Lineage ----
        self._lineage.record(
            trace_id=trace_id,
            operation="read",
            inputs={"source": self._config.model_dump(mode="json").get("data_source")},
            outputs={"dataframe_columns": list(df.columns)},
        )

        # ---- Phase 3 pipeline placeholders ----
        # profiling = ...
        # detections = ...
        # scores = ...
        # decision = ...

        return ADQAResult(
            dataframe=df,
            execution_mode=self._config.execution_mode.value,
            trace_id=str(trace_id),
            config_hash=snapshot.hash(),
        )

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _initialize_trace_session(
        self,
    ) -> tuple[UUID, NoOpTraceEmitter | TraceEmitter, ConfigSnapshot]:
        """
        Initialize trace context and emit start/snapshot events.
        """
        # Create trace context for this run
        trace_context = TraceContext()
        trace_id = trace_context.trace_id

        # Initialize emitter with this context
        trace_emitter = self._create_emitter(trace_context)

        # Emit trace context initialization
        trace_emitter.emit(
            TraceEvent(
                trace_id=trace_id,
                event_type=TraceEventType.START,
                name="TRACE_CONTEXT_INITIALIZED",
                metadata={
                    k: to_trace_value(v) for k, v in trace_context.to_dict().items()
                },
            )
        )

        # Emit config snapshot
        snapshot = snapshot_from_config(self._config)

        trace_emitter.emit(
            TraceEvent(
                trace_id=trace_id,
                event_type=TraceEventType.SNAPSHOT,
                name="CONFIG_SNAPSHOT",
                metadata={
                    "config": snapshot.to_json(),
                    "hash": snapshot.hash(),
                },
            )
        )

        return trace_id, trace_emitter, snapshot

    def _create_emitter(self, context: TraceContext) -> NoOpTraceEmitter | TraceEmitter:
        if not self._config.tracing_enabled:
            return NoOpTraceEmitter()

        store: InMemoryTraceStore | JSONTraceStore | None = None
        if self._config.trace_store == TraceStoreType.IN_MEMORY:
            store = InMemoryTraceStore()
        elif self._config.trace_store == TraceStoreType.JSONL:
            # Default to adqa_traces.jsonl since path isn't in config
            store = JSONTraceStore(file_path="adqa_traces.jsonl")

        return TraceEmitter(context=context, store=store, store_traces=True)

    def _init_lineage(self) -> NoOpLineageRecorder | LineageRecorder:
        if not self._config.lineage_enabled:
            return NoOpLineageRecorder()

        adapter = InMemoryLineageAdapter()
        recorder = LineageRecorder(adapter=adapter, enabled=True)
        return recorder
