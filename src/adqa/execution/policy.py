from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import Action, ActionPlan, ExecutionMode

if TYPE_CHECKING:
    from ..config.model import ADQAConfig
    from ..scoring.models import QualityDecision


class ExecutionPolicy:
    """
    Intelligent Agent Policy with Action De-confliction.
    Ensures a clean, professional remediation plan by resolving conflicting actions.
    """

    def evaluate(self, decision: QualityDecision, config: ADQAConfig) -> ActionPlan:
        mode = config.execution_mode
        raw_actions: list[Action] = []

        # 1. Gather all possible remediations
        raw_actions.extend(self._issue_based_actions(decision, config))

        # 2. De-conflict and Rank actions (Decisive Cleanup)
        actions = self._deconflict_actions(raw_actions)

        # 3. Add global governance actions (Block/Allow)
        if decision.severity_level == "CRITICAL" or decision.decision == "FAIL":
            actions.append(
                self._create_base_failure_action(decision, mode, decision.explanation)
            )
        elif decision.decision == "PASS" and not actions:
            actions.append(
                Action(
                    action_type="ALLOW",
                    reason="Data quality acceptable",
                    metadata={"decision": "PASS"},
                )
            )

        # 4. Advisory Mode override
        if mode == ExecutionMode.ADVISORY:
            for action in actions:
                if action.action_type in ("BLOCK", "REMEDIATE"):
                    action.reason = (
                        f"[ADVICE] Would perform {action.action_type}: {action.reason}"
                    )
                    action.action_type = "WARN"
                action.requires_approval = False

        return ActionPlan(
            actions=actions,
            requires_human=any(a.requires_approval for a in actions),
            summary=self._build_summary(decision, actions),
        )

    def _deconflict_actions(self, actions: list[Action]) -> list[Action]:
        """
        Ensures ONE primary remediation per column to avoid corruption.
        Priority: Drop > Transformation > Flagging
        """
        final_actions = []

        # 1. Separate actions by target
        dataset_actions = []
        column_actions: dict[str, list[Action]] = {}

        for a in actions:
            col = a.metadata.get("column")
            if not col or col == "DATASET":
                dataset_actions.append(a)
            else:
                column_actions.setdefault(col, []).append(a)

        # 2. Add all unique dataset actions
        seen_ds_ops = set()
        for a in dataset_actions:
            op = a.metadata.get("operation")
            if op not in seen_ds_ops:
                final_actions.append(a)
                seen_ds_ops.add(op)
        # 3. Handle Column-Specific Conflicts
        for _col, col_actions in column_actions.items():
            # A. Check if any action is a DROP
            drop_action = next(
                (
                    a
                    for a in col_actions
                    if a.metadata.get("operation") == "drop_column"
                ),
                None,
            )
            if drop_action:
                final_actions.append(drop_action)
                continue  # Skip all other fixes for this column

            # B. Pick ONE best transformation
            # Priority: Mask PII > Cast Type > Clip > Transform > Impute > Flag > Group
            priority = [
                "mask_pii",
                "cast_type",
                "clip",
                "log_transform",
                "impute",
                "flag_nulls",
                "group_rare",
            ]

            best_action = None
            best_rank = len(priority)

            for a in col_actions:
                op = a.metadata.get("operation", "warn")
                if op in priority:
                    rank = priority.index(op)
                    if rank < best_rank:
                        best_rank = rank
                        best_action = a

            if best_action:
                final_actions.append(best_action)
            else:
                # Add first warning or remediate action if no specific priority match
                warn_or_rem = next(
                    (a for a in col_actions if a.action_type in ("WARN", "REMEDIATE")),
                    None,
                )
                if warn_or_rem:
                    final_actions.append(warn_or_rem)

        return final_actions

    def _issue_based_actions(
        self, decision: QualityDecision, config: ADQAConfig
    ) -> list[Action]:
        actions = []
        mode = config.execution_mode

        for issue_type, columns in decision.issue_map.items():
            if issue_type == "missing_values":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.4:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Significant nulls {score:.0%})",
                                mode,
                            )
                        )
                    else:
                        actions.append(
                            self._remediate(
                                col,
                                "impute",
                                f"Impute {col} (Median)",
                                mode,
                                strategy="median",
                            )
                        )

            elif issue_type == "duplicate_rows":
                actions.append(
                    self._remediate(
                        None, "remove_duplicates", "Deduplicate dataset", mode
                    )
                )

            elif issue_type == "constant_column":
                for col in columns:
                    if col == "DATASET":
                        continue
                    actions.append(
                        self._remediate(
                            col, "drop_column", f"Drop constant column {col}", mode
                        )
                    )

            elif issue_type == "outliers":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.7:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Extreme outliers)",
                                mode,
                            )
                        )
                    else:
                        actions.append(
                            self._remediate(
                                col, "clip", f"Winsorize {col} (Clip outliers)", mode
                            )
                        )

            elif issue_type == "high_skewness":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.6:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Extreme skewness {score:.2f})",
                                mode,
                            )
                        )
                    else:
                        actions.append(
                            self._remediate(
                                col,
                                "log_transform",
                                f"Log-transform {col} to normalize",
                                mode,
                            )
                        )

            elif issue_type == "high_correlation":
                for col in columns:
                    if col == "DATASET":
                        continue
                    actions.append(
                        self._remediate(
                            col, "drop_column", f"Drop {col} (High correlation)", mode
                        )
                    )

            elif issue_type == "range_violation":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.5:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Severe range violations)",
                                mode,
                            )
                        )
                    else:
                        # Use clipping for range violations
                        min_v = config.detection.thresholds.min_value
                        max_v = config.detection.thresholds.max_value
                        actions.append(
                            self._remediate(
                                col,
                                "clip",
                                f"Clip {col} to valid range",
                                mode,
                                min=min_v,
                                max=max_v,
                            )
                        )

            elif issue_type == "zero_value":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.4:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Too many zeros {score:.2%})",
                                mode,
                            )
                        )
                    else:
                        actions.append(
                            self._remediate(
                                col,
                                "impute",
                                f"Impute {col} (Zeros detected)",
                                mode,
                                strategy="median",
                            )
                        )

            elif issue_type == "pattern_violation":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.5:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Severe pattern violations)",
                                mode,
                            )
                        )
                    else:
                        # For moderate violations, maybe flag?
                        actions.append(
                            self._remediate(
                                col,
                                "flag_nulls",
                                f"Flag pattern violations in {col}",
                                mode,
                            )
                        )

            elif issue_type == "data_drift":
                for col in columns:
                    if col == "DATASET":
                        continue
                    # Drift is often advisory unless extreme
                    actions.append(
                        Action(
                            action_type="WARN",
                            reason=f"Significant data drift detected in {col}",
                            metadata={"column": col, "operation": "warn"},
                        )
                    )

            elif issue_type == "quasi_identifier_risk":
                for col in columns:
                    if col == "DATASET":
                        continue
                    # Masking is safer for QI
                    actions.append(
                        self._remediate(
                            col,
                            "mask_pii",
                            f"Mask {col} to mitigate re-identification risk",
                            mode,
                        )
                    )

            elif issue_type == "semantic_violation":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.5:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Severe semantic violations)",
                                mode,
                            )
                        )
                    else:
                        actions.append(
                            self._remediate(
                                col, "clip", f"Clip {col} to semantic boundaries", mode
                            )
                        )

            elif issue_type == "imbalance":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.9:
                        actions.append(
                            self._remediate(
                                col,
                                "drop_column",
                                f"Drop {col} (Extreme imbalance {score:.2%})",
                                mode,
                            )
                        )
                    else:
                        actions.append(
                            self._remediate(
                                col, "group_rare", f"Merge rare labels in {col}", mode
                            )
                        )

            elif issue_type == "rare_category":
                for col in columns:
                    if col == "DATASET":
                        continue
                    actions.append(
                        self._remediate(
                            col, "group_rare", f"Merge rare labels in {col}", mode
                        )
                    )

            elif issue_type == "type_mismatch":
                for col in columns:
                    if col == "DATASET":
                        continue
                    actions.append(
                        self._remediate(
                            col,
                            "cast_type",
                            f"Repair schema for {col}",
                            mode,
                            target_type="numeric",
                        )
                    )

            elif issue_type == "pii_detected":
                for col in columns:
                    if col == "DATASET":
                        continue
                    score = decision.column_breakdown.get(col, 0)
                    if score > 0.8:
                        actions.append(
                            self._remediate(
                                col, "drop_column", f"Drop {col} (Sensitive PII)", mode
                            )
                        )
                    else:
                        actions.append(
                            self._remediate(
                                col, "mask_pii", f"Anonymize PII in {col}", mode
                            )
                        )

            elif issue_type == "anomaly_score":
                # Get indices from decision metadata if available
                metadata = decision.issue_metadata.get("anomaly_score", {})
                indices = metadata.get("indices") or []
                actions.append(
                    self._remediate(
                        None,
                        "remove_anomalies",
                        "Drop anomalous records",
                        mode,
                        indices=indices,
                    )
                )

        return actions

    def _remediate(
        self,
        col: str | None,
        op: str,
        reason: str,
        mode: str | ExecutionMode,
        **kwargs: Any,
    ) -> Action:
        meta = {"operation": op, "column": col}
        meta.update(kwargs)

        # In Advisory or Human-in-loop, we don't apply automatically
        requires_approval = mode in (
            ExecutionMode.HUMAN_IN_LOOP,
            ExecutionMode.ADVISORY,
        )

        # Map operation to a friendly action type for display
        type_map = {
            "drop_column": "DROP",
            "remove_duplicates": "DEDUPE",
            "impute": "IMPUTE",
            "clip": "CLIP",
            "log_transform": "TRANSFORM",
            "group_rare": "GROUP",
            "cast_type": "REPAIR",
            "mask_pii": "MASK",
            "remove_anomalies": "DROP",
            "flag_nulls": "FLAG",
        }
        action_type = type_map.get(op, "REMEDIATE")

        return Action(
            action_type=action_type,
            reason=reason,
            requires_approval=requires_approval,
            metadata=meta,
        )

    def _create_base_failure_action(
        self, decision: QualityDecision, mode: str, reason: str
    ) -> Action:
        if mode == ExecutionMode.AUTOMATIC:
            return Action(
                action_type="BLOCK",
                reason=f"Pipeline Blocked: {reason}",
                requires_approval=False,
            )

        # In advisory/human-in-loop, a BLOCK is a proposal that
        # needs to be "confirmed" or "accepted"
        return Action(
            action_type="BLOCK", reason=f"Critical: {reason}", requires_approval=True
        )

    def _build_summary(self, decision: QualityDecision, actions: list[Action]) -> str:
        types = [a.action_type for a in actions]
        return f"{decision.decision} ({decision.score:.2f}) -> {', '.join(set(types))}"
