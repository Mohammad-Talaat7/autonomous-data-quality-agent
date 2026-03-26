from .models import AggregatedScore, QualityDecision
from .thresholds import Thresholds


class DecisionEngine:
    def decide(self, agg: AggregatedScore) -> QualityDecision:
        score = agg.global_score

        # -------- decision --------
        if score < Thresholds.PASS:
            decision = "PASS"
        elif score < Thresholds.WARN:
            decision = "WARN"
        else:
            decision = "FAIL"

        # -------- severity level --------
        severity_level = self._compute_severity(score)

        # -------- dominant factors --------
        dominant_issues = sorted(
            agg.issue_breakdown.keys(),
            key=lambda k: float(agg.issue_breakdown[k]),
            reverse=True,
        )[:2]

        dominant_dimensions = sorted(
            agg.dimension_breakdown.keys(),
            key=lambda k: float(agg.dimension_breakdown[k]),
            reverse=True,
        )[:2]

        affected_columns = sorted(
            agg.column_breakdown.keys(),
            key=lambda k: float(agg.column_breakdown[k]),
            reverse=True,
        )[:3]

        explanation = self._build_explanation(
            decision, score, dominant_issues, dominant_dimensions, affected_columns
        )

        return QualityDecision(
            decision=decision,
            score=score,
            severity_level=severity_level,
            breakdown=agg.issue_breakdown,
            dimension_breakdown=agg.dimension_breakdown,
            dominant_issues=dominant_issues,
            affected_columns=affected_columns,
            thresholds_used={
                "pass": Thresholds.PASS,
                "warn": Thresholds.WARN,
            },
            explanation=explanation,
        )

    def _compute_severity(self, score: float) -> str:
        levels = Thresholds.LEVELS

        if score >= levels["CRITICAL"]:
            return "CRITICAL"
        elif score >= levels["HIGH"]:
            return "HIGH"
        elif score >= levels["MEDIUM"]:
            return "MEDIUM"
        return "LOW"

    def _build_explanation(
        self,
        decision: str,
        score: float,
        issues: list[str],
        dims: list[str],
        columns: list[str],
    ) -> str:
        msg = f"Data quality is {decision} with a risk score of {score:.3f}. "

        if issues:
            msg += f"Primary issues identified: {', '.join(issues)}. "

        if dims:
            msg += f"Most affected quality dimensions: {', '.join(dims)}. "

        if columns:
            msg += f"Top columns requiring attention: {', '.join(columns)}."

        return msg
