from collections import defaultdict

from ..models import AggregatedScore, Score


class Aggregator:
    def aggregate(self, scores: list[Score]) -> AggregatedScore:
        if not scores:
            return AggregatedScore(
                global_score=0.0,
                issue_breakdown={},
                column_breakdown={},
                dimension_breakdown={},
                raw_scores=[],
            )

        total_weight = sum(s.weight for s in scores)
        max_score = max(s.final_score for s in scores)

        weighted_mean = (
            sum(s.final_score for s in scores) / total_weight
            if total_weight > 0
            else 0.0
        )

        # -------- global score calculation --------
        # Use a "Severity-Aware" aggregation:
        # One critical issue should pull the whole dataset into WARN or FAIL.
        # We take the max of the mean risk and a percentage of the max risk.
        global_score = max(weighted_mean, max_score * 0.8)

        # -------- issue breakdown --------
        issue_groups = defaultdict(list)
        for s in scores:
            issue_groups[s.issue_type].append(s)

        issue_breakdown = {
            issue: sum(s.final_score for s in group) / len(group)
            for issue, group in issue_groups.items()
        }

        # -------- column breakdown --------
        column_groups = defaultdict(list)
        for s in scores:
            if s.column:
                column_groups[s.column].append(s)

        column_breakdown = {
            col: sum(s.final_score for s in group) / len(group)
            for col, group in column_groups.items()
        }

        # -------- dimension breakdown --------
        dimension_groups = defaultdict(list)
        for s in scores:
            dimension_groups[s.dimension].append(s)

        dimension_breakdown = {
            dim: sum(s.final_score for s in group) / len(group)
            for dim, group in dimension_groups.items()
        }

        return AggregatedScore(
            global_score=global_score,
            issue_breakdown=issue_breakdown,
            column_breakdown=column_breakdown,
            dimension_breakdown=dimension_breakdown,
            raw_scores=scores,
        )
