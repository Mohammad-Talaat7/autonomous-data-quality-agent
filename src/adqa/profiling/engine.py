from __future__ import annotations

import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..config.model import ADQAConfig

import pandas as pd

from ..trace.enums import TraceEventType
from ..trace.events import TraceEvent
from ..trace.noop import NoOpLineageRecorder, NoOpTraceEmitter
from .cache import ProfileCache
from .ml.ml_profiler import run_ml_profiling
from .models.column_profile import ColumnProfile
from .models.dataset_profile import DatasetProfile
from .models.ml_profile import MLProfile
from .models.profiling_result import ProfilingResult
from .relational.correlation_profiler import profile_correlations
from .signals.risk_signal_builder import build_risk_signals
from .structural.column_profiler import profile_column
from .structural.dataset_profiler import profile_dataset_structure
from .utils.hashing import hash_dataframe
from .utils.rounding import round_value


class ProfilingEngine:
    """
    Synchronous deterministic profiling engine.
    ML profiling is optional and isolated.
    """

    def __init__(
        self,
        config: ADQAConfig,
        cache: ProfileCache | None = None,
        tracer: NoOpTraceEmitter | Any | None = None,
        lineage: NoOpLineageRecorder | Any | None = None,
    ):
        self._config = config
        self._profiling_config = config.profiling
        self._cache = cache
        self._tracer = tracer or NoOpTraceEmitter()
        self._lineage = lineage or NoOpLineageRecorder()

    # =========================
    # Public API
    # =========================

    def run(self, df: pd.DataFrame) -> ProfilingResult:
        """
        Execute full profiling pipeline with deterministic caching and tracing.
        """

        start_time = time.perf_counter()

        # =========================
        # Hash + Cache Key
        # =========================

        df_hash = hash_dataframe(df, fast=True)

        config_repr = (
            self._profiling_config.model_dump_json()
            if hasattr(self._profiling_config, "model_dump_json")
            else str(self._profiling_config)
        )

        cache_key = f"{df_hash}:{config_repr}"

        self._tracer.emit(
            TraceEvent(
                trace_id=self._tracer.context.trace_id,
                event_type=TraceEventType.PROFILING,
                name="PROFILE_DATASET_START",
                metadata={
                    "rows": len(df),
                    "columns": len(df.columns),
                    "df_hash": df_hash,
                },
            )
        )

        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._tracer.emit(
                    TraceEvent(
                        trace_id=self._tracer.context.trace_id,
                        event_type=TraceEventType.PROFILING,
                        name="PROFILE_CACHE_HIT",
                        metadata={"df_hash": df_hash},
                    )
                )
                return cached

        # =========================
        # Sampling for expensive metrics
        # =========================

        df_for_expensive_metrics = df
        if len(df) > self._profiling_config.sampling_threshold:
            df_for_expensive_metrics = df.sample(
                n=min(self._profiling_config.sample_size, len(df)),
                random_state=self._profiling_config.thresholds.global_seed,
            )
            self._tracer.emit(
                TraceEvent(
                    trace_id=self._tracer.context.trace_id,
                    event_type=TraceEventType.PROFILING,
                    name="PROFILE_SAMPLING_APPLIED",
                    metadata={
                        "original_rows": len(df),
                        "sample_rows": len(df_for_expensive_metrics),
                    },
                )
            )

        # =========================
        # Structural Profiling (Full Data)
        # =========================

        t0 = time.perf_counter()
        dataset_metadata = profile_dataset_structure(df)
        column_profiles = self._profile_columns(df)
        structural_duration = time.perf_counter() - t0

        self._tracer.emit(
            TraceEvent(
                trace_id=self._tracer.context.trace_id,
                event_type=TraceEventType.PROFILING,
                name="PROFILE_STRUCTURAL_DONE",
                metadata={
                    "duration_sec": structural_duration,
                    "column_count": len(column_profiles),
                },
            )
        )

        # =========================
        # Correlation Profiling (Sampled Data if large)
        # =========================

        correlation_profile = None
        if self._profiling_config.enable_correlation:
            t0 = time.perf_counter()
            correlation_profile = profile_correlations(
                df=df_for_expensive_metrics,
                columns=column_profiles,
                method=self._profiling_config.correlation_method,
                thresholds=self._profiling_config.thresholds,
            )
            corr_duration = time.perf_counter() - t0

            self._tracer.emit(
                TraceEvent(
                    trace_id=self._tracer.context.trace_id,
                    event_type=TraceEventType.PROFILING,
                    name="PROFILE_CORRELATION_DONE",
                    metadata={
                        "duration_sec": corr_duration,
                        "method": self._profiling_config.correlation_method,
                        "pair_count": (
                            len(correlation_profile.matrix)
                            if correlation_profile
                            else 0
                        ),
                        "sampled": len(df) > self._profiling_config.sampling_threshold,
                    },
                )
            )

        # =========================
        # Risk Signals
        # =========================

        t0 = time.perf_counter()
        risk_signals = build_risk_signals(
            metadata=dataset_metadata,
            columns=column_profiles,
            correlations=correlation_profile,
        )
        signal_duration = time.perf_counter() - t0

        self._tracer.emit(
            TraceEvent(
                trace_id=self._tracer.context.trace_id,
                event_type=TraceEventType.PROFILING,
                name="PROFILE_RISK_SIGNALS_DONE",
                metadata={
                    "duration_sec": signal_duration,
                    "signal_count": len(risk_signals),
                },
            )
        )

        # =========================
        # ML Profiling
        # =========================

        ml_profiles = None

        if getattr(self._profiling_config, "enable_ml", False):
            t0 = time.perf_counter()
            ml_profiles = self._run_ml_profiling(
                df_for_expensive_metrics, column_profiles
            )
            ml_duration = time.perf_counter() - t0

            self._tracer.emit(
                TraceEvent(
                    trace_id=self._tracer.context.trace_id,
                    event_type=TraceEventType.PROFILING,
                    name="ML_PROFILE_RUN",
                    metadata={
                        "duration_sec": ml_duration,
                        "ml_profile_count": len(ml_profiles),
                    },
                )
            )

        # =========================
        # Rounding
        # =========================

        precision = self._profiling_config.rounding_precision

        dataset_profile = DatasetProfile(
            metadata=dataset_metadata,
            columns=column_profiles,
            correlations=correlation_profile,
        )

        dataset_profile = round_value(dataset_profile, precision)
        risk_signals = round_value(risk_signals, precision)

        if ml_profiles:
            ml_profiles = round_value(ml_profiles, precision)

        result = ProfilingResult(
            dataset_profile=dataset_profile,
            risk_signals=risk_signals,
            ml_profiles=ml_profiles,
        )

        # =========================
        # Cache Store
        # =========================

        if self._cache:
            self._cache.set(cache_key, result)

        profile_id = self._generate_profile_id(cache_key)

        self._lineage.record(
            trace_id=self._tracer.context.trace_id,
            operation="profiling",
            inputs={"dataframe_hash": df_hash},
            outputs={"profile_id": profile_id},
            metadata={
                "row_count": dataset_metadata.row_count,
                "column_count": dataset_metadata.column_count,
                "ml_enabled": bool(ml_profiles),
            },
        )

        if ml_profiles:
            for ml in ml_profiles:
                ml_id = hashlib.sha256(
                    f"ml:{profile_id}:{ml.target}:{ml.model_name}".encode()
                ).hexdigest()

                self._lineage.record(
                    trace_id=self._tracer.context.trace_id,
                    operation=f"ml_{ml.model_name}",
                    inputs={"profile_id": profile_id, "target": ml.target},
                    outputs={"ml_id": ml_id},
                    metadata={
                        "target": ml.target,
                        "model_version": ml.model_version,
                    },
                )

        total_duration = time.perf_counter() - start_time

        self._tracer.emit(
            TraceEvent(
                trace_id=self._tracer.context.trace_id,
                event_type=TraceEventType.PROFILING,
                name="PROFILE_DATASET_END",
                metadata={
                    "duration_sec": total_duration,
                    "df_hash": df_hash,
                    "profile_id": profile_id,
                    "signal_count": len(risk_signals),
                    "ml_enabled": bool(ml_profiles),
                },
            )
        )

        return result

    # =========================
    # Internal Helpers
    # =========================

    def _profile_columns(self, df: pd.DataFrame) -> tuple[ColumnProfile, ...]:
        max_workers = self._profiling_config.max_workers
        thresholds = self._profiling_config.thresholds

        # Parallel processing if multiple workers allowed and enough columns
        if max_workers is not None and max_workers > 1 and len(df.columns) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Need to use a lambda or partial to pass thresholds
                from functools import partial

                profile_func = partial(profile_column, thresholds=thresholds)
                profiles = list(
                    executor.map(profile_func, [df[col] for col in df.columns])
                )
        else:
            profiles = []
            for column_name in df.columns:
                series = df[column_name]
                profile = profile_column(series, thresholds=thresholds)
                profiles.append(profile)

        # Deterministic ordering
        profiles.sort(key=lambda p: p.name)

        return tuple(profiles)

    def _generate_profile_id(self, cache_key: str) -> str:
        return hashlib.sha256(f"profile:{cache_key}".encode()).hexdigest()

    def _run_ml_profiling(
        self,
        df: pd.DataFrame,
        columns: tuple[ColumnProfile, ...],
    ) -> tuple[MLProfile, ...]:

        return run_ml_profiling(
            df=df,
            column_profiles=columns,
            random_state=getattr(self._config, "global_seed", 42),
            thresholds=self._profiling_config.thresholds,
        )
