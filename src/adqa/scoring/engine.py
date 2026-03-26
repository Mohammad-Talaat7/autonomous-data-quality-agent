from typing import Any

from .aggregation.aggregator import Aggregator
from .decision import DecisionEngine
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

    def run(self, detection_results: Any, ml_evidence: Any = None) -> Any:
        """
        Execute the scoring pipeline.
        Supports both individual lists and DetectionResultBundle.
        """
        # Support DetectionResultBundle if passed as first argument
        is_bundle = hasattr(detection_results, "detections") and hasattr(
            detection_results, "ml_evidence"
        )
        if is_bundle:
            bundle = detection_results
            detection_results = bundle.detections
            if ml_evidence is None:
                ml_evidence = bundle.ml_evidence

        # -------- normalize --------
        normalized = normalize_detection_results(detection_results, ml_evidence)

        scores = []

        # -------- scoring --------
        for d in normalized:
            score = self.scorer.compute(d)

            if self.tracer:
                self.tracer.trace(
                    "COMPUTE_SCORE",
                    {
                        "detector_id": d.detector_id,
                        "rule_id": d.rule_id,
                        "dimension": d.dimension,
                        "final_score": score.final_score,
                    },
                )

            scores.append(score)

        # -------- aggregation --------
        agg = self.aggregator.aggregate(scores)

        if self.tracer:
            self.tracer.trace(
                "AGGREGATE_SCORE",
                {
                    "global_score": agg.global_score,
                    "num_scores": len(scores),
                },
            )

        # -------- decision --------
        decision = self.decision_engine.decide(agg)

        if self.tracer:
            self.tracer.trace(
                "QUALITY_DECISION",
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
            if detection_results:
                inputs.extend(detection_results)
            if ml_evidence:
                inputs.extend(ml_evidence)

            self.lineage.record("quality_decision", inputs=inputs, outputs=decision)

        return decision
