# adqa/api.py

from __future__ import annotations

from typing import Any
from uuid import UUID

import pandas as pd

from ..config import ADQAConfig, ConfigSnapshot, TraceStoreType, snapshot_from_config
from ..data_ingress.datasource import DataSource
from ..data_ingress.factory import DataReaderFactory
from ..data_ingress.reader import DataReader
from ..detection import DetectionEngine, build_registry
from ..execution import ActionPlan, ExecutionEngine
from ..profiling.cache import ProfileCache
from ..profiling.engine import ProfilingEngine
from ..scoring import ScoringEngine
from ..trace.context import TraceContext
from ..trace.emitter import TraceEmitter
from ..trace.enums import TraceComponent, TraceEventType
from ..trace.events import TraceEvent
from ..trace.hooks.serialize import to_trace_value
from ..trace.lineage import LineageRecorder
from ..trace.lineage.memory import InMemoryLineageAdapter
from ..trace.noop import NoOpLineageRecorder, NoOpTraceEmitter
from ..trace.store import InMemoryTraceStore, JSONTraceStore
from .result import ADQAResult


class ADQA:
    """
    Public entry point for ADQA.
    Orchestrates the Phase 3 pipeline.
    """

    def __init__(
        self,
        *,
        data_source: DataSource,
        config: ADQAConfig | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        historical_profiles: Any | None = None,
    ):
        self._config: ADQAConfig = config or ADQAConfig()
        self._data_source: DataSource = data_source
        self._tags = tags or []
        self._metadata = metadata or {}
        self._historical_profiles = historical_profiles

        # Build reader early → fail fast
        self._reader: DataReader = DataReaderFactory.create(self._data_source)

        # Lineage setup
        self._lineage: NoOpLineageRecorder | LineageRecorder = self._init_lineage()

        # Profiling setup
        self._cache = ProfileCache()
        self._profiler = ProfilingEngine(
            config=self._config,
            cache=self._cache,
            lineage=self._lineage,
        )

        # Detection setup
        registry = build_registry()
        thresholds = self._config.detection.thresholds

        ml_detectors = []
        if self._config.ml_enabled and self._config.detection.enable_ml:
            ml_detectors = registry.create_ml_detectors(thresholds=thresholds)

        self._detection_engine = DetectionEngine(
            rule_detectors=registry.create_rule_detectors(thresholds=thresholds),
            ml_detectors=ml_detectors,
            lineage=self._lineage,
        )

        # Scoring setup
        self._scoring_engine = ScoringEngine(
            lineage=self._lineage,
            weight_map=self._config.scoring.weight_map,
        )

        # Execution setup
        self._execution_engine = ExecutionEngine(lineage=self._lineage)

    @staticmethod
    def from_path(
        path: str,
        config: ADQAConfig | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        historical_profiles: Any | None = None,
    ) -> ADQA:
        """
        Quick-start from a local or remote path.
        """
        source = DataSource.load(path)
        return ADQA(
            data_source=source,
            config=config,
            tags=tags,
            metadata=metadata,
            historical_profiles=historical_profiles,
        )

    @staticmethod
    def from_df(
        df: pd.DataFrame,
        config: ADQAConfig | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        historical_profiles: Any | None = None,
    ) -> ADQA:
        """
        Quick-start from an existing pandas DataFrame.
        """
        source = DataSource.from_df(df)
        return ADQA(
            data_source=source,
            config=config,
            tags=tags,
            metadata=metadata,
            historical_profiles=historical_profiles,
        )

    def on_action(self, action_type: str, handler: Any) -> ADQA:
        """
        Register a custom side-effect handler for an action (e.g. BLOCK, WARN).
        Returns self for fluent chaining.
        """
        self._execution_engine.executor.register_handler(action_type, handler)
        return self

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def analyze(
        self, profile_override: Any = None, historical_profiles: Any | None = None
    ) -> ADQAResult:
        """
        Run ADQA analysis.
        Orchestrates full Phase 3 pipeline:
        Ingress -> Profiling -> Detection -> Scoring -> Execution.
        """
        trace_id, trace_emitter, snapshot = self._initialize_trace_session()

        hist = historical_profiles or self._historical_profiles

        with trace_emitter.span("ADQA_ANALYZE", component=TraceComponent.TRACE):
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
                inputs={
                    "source": (
                        self._data_source.config.model_dump(mode="json")
                        if hasattr(self._data_source.config, "model_dump")
                        else str(self._data_source.config)
                    )
                },
                outputs={"dataframe_columns": list(df.columns)},
            )

            # ---- Profiling ----
            self._profiler._tracer = trace_emitter
            if profile_override is not None:
                profiling_result = profile_override
                trace_emitter.trace("PROFILE_OVERRIDE_APPLIED")
            else:
                profiling_result = self._profiler.run(df)

            # ---- Detection ----
            self._detection_engine.tracing = trace_emitter
            column_profiles_map = {
                p.name: p for p in profiling_result.dataset_profile.columns
            }
            detections = self._detection_engine.run(
                dataset_profile=profiling_result.dataset_profile,
                column_profiles=column_profiles_map,
                ml_profiles=profiling_result.ml_profiles,
                raw_data_sample=df,
                historical_profiles=hist,
            )

            # ---- Scoring ----
            self._scoring_engine.tracer = trace_emitter
            scoring_result = self._scoring_engine.run(detections)

            # ---- Execution ----
            self._execution_engine.tracer = trace_emitter
            execution_result, remediated_df = self._execution_engine.run(
                scoring_result.decision, self._config, df=df
            )

            return ADQAResult(
                dataframe=remediated_df if remediated_df is not None else df,
                profiles=profiling_result,
                detections=detections,
                scores=scoring_result.aggregated,
                decision=scoring_result.decision,
                execution_mode=self._config.execution_mode.value,
                actions=execution_result.executed_actions,
                blocked=execution_result.blocked,
                plan=execution_result.plan,
                approval_payload=execution_result.approval_payload,
                trace_id=str(trace_id),
                config_hash=snapshot.hash(),
            )

    def execute_plan(
        self, plan: ActionPlan, df: pd.DataFrame | None = None
    ) -> ADQAResult:
        """
        Execute an ActionPlan that has been approved
        (e.g. from a previous analyze() run).
        """
        # We need a trace session for this standalone execution run
        trace_id, trace_emitter, snapshot = self._initialize_trace_session()

        with trace_emitter.span("ADQA_EXECUTE_PLAN", component=TraceComponent.TRACE):
            self._execution_engine.tracer = trace_emitter
            result, remediated_df = self._execution_engine.execute_plan(plan, df=df)

            return ADQAResult(
                dataframe=remediated_df,
                execution_mode=self._config.execution_mode.value,
                actions=result.executed_actions,
                blocked=result.blocked,
                plan=plan,
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
        trace_metadata: dict[str, Any] = {
            k: to_trace_value(v) for k, v in trace_context.to_dict().items()
        }
        trace_metadata["tags"] = [to_trace_value(t) for t in self._tags]
        trace_metadata.update(self._metadata)

        trace_emitter.emit(
            TraceEvent(
                trace_id=trace_id,
                event_type=TraceEventType.START,
                name="TRACE_CONTEXT_INITIALIZED",
                metadata=trace_metadata,
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
