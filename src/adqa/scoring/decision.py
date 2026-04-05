from typing import Any

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
        # Include all issues with significant risk (> 0.1) instead of just top 2
        all_issues = sorted(
            agg.issue_breakdown.keys(),
            key=lambda k: float(agg.issue_breakdown[k]),
            reverse=True,
        )
        dominant_issues = [i for i in all_issues if agg.issue_breakdown[i] > 0.1][:5]
        if not dominant_issues and all_issues:
            dominant_issues = all_issues[:1]

        all_dims = sorted(
            agg.dimension_breakdown.keys(),
            key=lambda k: float(agg.dimension_breakdown[k]),
            reverse=True,
        )
        dominant_dimensions = [d for d in all_dims if agg.dimension_breakdown[d] > 0.1][
            :3
        ]
        if not dominant_dimensions and all_dims:
            dominant_dimensions = all_dims[:1]

        all_cols = sorted(
            agg.column_breakdown.keys(),
            key=lambda k: float(agg.column_breakdown[k]),
            reverse=True,
        )
        affected_columns = [c for c in all_cols if agg.column_breakdown[c] > 0.1][:5]
        if not affected_columns and all_cols:
            affected_columns = all_cols[:1]

        explanation = self._build_explanation(
            decision, score, dominant_issues, dominant_dimensions, affected_columns
        )

        # Build issue map (issue_type -> [cols])
        issue_map: dict[str, list[str]] = {}
        issue_metadata: dict[str, dict[str, Any]] = {}

        for s in agg.raw_scores:
            cols = issue_map.setdefault(s.issue_type, [])
            if s.column and s.column not in cols:
                cols.append(s.column)
            elif not s.column and "DATASET" not in cols:
                # Use a placeholder for dataset-level issues
                cols.append("DATASET")

            # Merge metadata for the issue type
            if s.metadata:
                issue_metadata.setdefault(s.issue_type, {}).update(s.metadata)

        return QualityDecision(
            decision=decision,
            score=score,
            severity_level=severity_level,
            breakdown=agg.issue_breakdown,
            dimension_breakdown=agg.dimension_breakdown,
            column_breakdown=agg.column_breakdown,
            issue_map=issue_map,
            issue_metadata=issue_metadata,
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
