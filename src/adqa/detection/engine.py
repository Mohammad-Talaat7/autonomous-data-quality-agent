# detection/engine.py

from typing import Any

from ..trace.noop import NoOpLineageRecorder, NoOpTraceEmitter
from .base import BaseDetector, BaseMLDetector
from .context import DetectionContext
from .results import DetectionResult, DetectionResultBundle, MLEvidence


class DetectionEngine:
    def __init__(
        self,
        rule_detectors: list[BaseDetector],
        ml_detectors: list[BaseMLDetector],
        tracing: Any = None,
        lineage: Any = None,
    ) -> None:
        self.rule_detectors = rule_detectors
        self.ml_detectors = ml_detectors

        self.tracing = tracing or NoOpTraceEmitter()
        self.lineage = lineage or NoOpLineageRecorder()

    # =========================
    # Public API
    # =========================

    def run(
        self,
        dataset_profile: Any,
        column_profiles: dict[str, Any],
        ml_profiles: Any | None = None,
        raw_data_sample: Any | None = None,
    ) -> DetectionResultBundle:
        # Extract correlation matrix if available in dataset_profile
        correlation_matrix = None
        if hasattr(dataset_profile, "correlations") and dataset_profile.correlations:
            correlation_matrix = getattr(dataset_profile.correlations, "matrix", None)

        context = DetectionContext(
            dataset_profile=dataset_profile,
            column_profiles=column_profiles,
            ml_profiles=ml_profiles,
            correlation_matrix=correlation_matrix,
            raw_data_sample=raw_data_sample,
        )

        bundle = DetectionResultBundle()

        # -------------------------
        # Rule-based detection
        # -------------------------
        for rule_det in self.rule_detectors:
            results = self._run_rule_detector(rule_det, context)
            bundle.detections.extend(results)

        # -------------------------
        # ML-based detection
        # -------------------------
        for ml_det in self.ml_detectors:
            evidence = self._run_ml_detector(ml_det, context)
            bundle.ml_evidence.extend(evidence)

        return bundle

    # =========================
    # Internal Execution
    # =========================

    def _run_rule_detector(
        self, detector: BaseDetector, context: DetectionContext
    ) -> list[DetectionResult]:
        if self.tracing:
            with self.tracing.span(
                "RUN_DETECTOR", detector=detector.__class__.__name__
            ):
                results = detector.detect(context)
        else:
            results = detector.detect(context)

        for r in results:
            if hasattr(detector, "dimension") and r.dimension == "unknown":
                r.dimension = detector.dimension

        self._register_lineage(context, results)

        return results

    def _run_ml_detector(
        self, detector: BaseMLDetector, context: DetectionContext
    ) -> list[MLEvidence]:
        if not context.has_ml():
            return []

        if self.tracing:
            with self.tracing.span("ML_MODEL_RUN", model=detector.__class__.__name__):
                evidence = detector.run_model(context)
        else:
            evidence = detector.run_model(context)

        for e in evidence:
            if hasattr(detector, "dimension") and e.dimension == "accuracy":
                e.dimension = detector.dimension

        self._register_lineage(context, evidence)

        return evidence

    # =========================
    # Lineage Handling
    # =========================

    def _register_lineage(self, context: DetectionContext, outputs: Any) -> None:
        if not self.lineage or isinstance(self.lineage, NoOpLineageRecorder):
            return

        # Attempt to get trace_id from tracing context if available
        trace_id = None
        if hasattr(self.tracing, "context") and hasattr(
            self.tracing.context, "trace_id"
        ):
            trace_id = self.tracing.context.trace_id

        if not trace_id:
            return

        for output in outputs:
            try:
                op_name = "unknown_detection"
                if hasattr(output, "detector_name"):
                    op_name = f"detection_{output.detector_name}"
                elif hasattr(output, "model_name"):
                    op_name = f"ml_{output.model_name}"

                self.lineage.record(
                    trace_id=trace_id,
                    operation=op_name,
                    # We use inputs/outputs loosely as nodes here
                    inputs={"dataset_profile": str(context.dataset_profile)},
                    outputs={"detection_id": getattr(output, "id", None)},
                    metadata={
                        "issue_type": getattr(output, "issue_type", None),
                        "score": getattr(output, "score", None),
                    },
                )
            except Exception:
                # Never break pipeline due to lineage
                pass
