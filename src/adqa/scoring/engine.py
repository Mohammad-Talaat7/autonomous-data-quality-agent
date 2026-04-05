from typing import Any

from .aggregation.aggregator import Aggregator
from .decision import DecisionEngine
from .models import ScoringResult
from .normalizer import normalize_detection_results
from .scorers.rule_scorer import RuleScorer


class ScoringEngine:
    def __init__(
        self,
        tracer: Any = None,
        lineage: Any = None,
        weight_map: dict[str, float] | None = None,
    ) -> None:
        self.tracer = tracer
        self.lineage = lineage

        self.scorer = RuleScorer(weight_map)
        self.aggregator = Aggregator()
        self.decision_engine = DecisionEngine()

    def run(self, detection_results: Any, ml_evidence: Any = None) -> ScoringResult:
        """
        Execute the scoring pipeline.
        Supports both individual lists and DetectionResultBundle.
        """
        # Support DetectionResultBundle if passed as first argument
        if hasattr(detection_results, "detections"):
            rules = detection_results.detections
            ml = detection_results.ml_evidence
        else:
            rules = detection_results
            ml = ml_evidence or []

        # 1. Normalize both Rules and ML
        normalized = normalize_detection_results(rules, ml_evidence=ml)

        # 2. Score
        scores = [self.scorer.compute(d) for d in normalized]

        if self.tracer:
            self.tracer.trace(
                "SCORING_DONE",
                {
                    "num_scores": len(scores),
                },
            )

        # 3. Aggregate
        agg = self.aggregator.aggregate(scores)

        # -------- decision --------
        decision = self.decision_engine.decide(agg)

        if self.tracer:
            self.tracer.trace(
                "DECISION_MADE",
                {
                    "decision": decision.decision,
                    "score": decision.score,
                    "severity": decision.severity_level,
                },
            )

        # -------- lineage --------
        if self.lineage:
            # Record decision lineage
            inputs = []
            if rules:
                inputs.extend(rules)
            if ml:
                inputs.extend(ml)

            trace_id = getattr(getattr(self.tracer, "context", None), "trace_id", None)
            if trace_id:
                self.lineage.record(
                    trace_id=trace_id,
                    operation="quality_decision",
                    inputs=inputs,
                    outputs=decision,
                )

        return ScoringResult(aggregated=agg, decision=decision)
