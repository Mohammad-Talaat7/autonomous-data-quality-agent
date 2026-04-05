from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from .models import Action, ActionPlan, ExecutionResult

ActionHandler = Callable[[Action, Any, pd.DataFrame | None], pd.DataFrame | None]


class ActionExecutor:
    """
    Comprehensive healing engine.
    Implements multiple tiered solutions for every detectable data quality issue.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register_handler(self, action_type: str, handler: ActionHandler) -> None:
        self._handlers[action_type] = handler

    def execute(
        self, plan: ActionPlan, tracer: Any = None, df: pd.DataFrame | None = None
    ) -> tuple[ExecutionResult, pd.DataFrame | None]:
        executed = []
        approval_requested = False
        blocked = False
        current_df = df

        for action in plan.actions:
            if tracer:
                tracer.trace(
                    "ACTION_START",
                    {"action_type": action.action_type, "reason": action.reason},
                )

            if action.requires_approval and not plan.approved:
                approval_requested = True
                continue

            # -------- 1. Custom Handlers --------
            handler = self._handlers.get(action.action_type)
            if handler:
                try:
                    new_df = handler(action, tracer, current_df)
                    if new_df is not None:
                        current_df = new_df
                except Exception as e:
                    if tracer:
                        tracer.trace("ACTION_HANDLER_ERROR", {"error": str(e)})

            # -------- 2. Built-in Multi-Solution Healing --------
            is_remediation = action.action_type not in (
                "BLOCK",
                "ALLOW",
                "WARN",
                "LOG",
                "REQUEST_APPROVAL",
            )
            if is_remediation and current_df is not None:
                current_df = self._perform_remediation(action, current_df, tracer)

            executed.append(action)

            if action.action_type == "BLOCK":
                blocked = True
                break

        result = ExecutionResult(
            executed_actions=executed,
            approval_requested=approval_requested,
            blocked=blocked,
            advisory=self._build_advisory(plan),
        )
        return result, current_df

    def _perform_remediation(
        self, action: Action, df: pd.DataFrame, tracer: Any
    ) -> pd.DataFrame:
        op = action.metadata.get("operation")
        col = action.metadata.get("column")

        if tracer:
            tracer.trace("REMEDIATION_START", {"operation": op, "column": col})

        try:
            # --- 1. Removal Operations ---
            if op == "drop_column":
                if col in df.columns:
                    df = df.drop(columns=[col])
                elif tracer:
                    tracer.trace(
                        "REMEDIATION_SKIPPED",
                        {"reason": f"Column {col} not found", "operation": op},
                    )

            elif op == "remove_duplicates":
                df = df.drop_duplicates()

            # --- 2. Imputation Operations ---
            elif op == "impute" and col in df.columns:
                strategy = action.metadata.get("strategy", "median")
                if strategy == "median":
                    df[col] = df[col].fillna(df[col].median())
                elif strategy == "mean":
                    df[col] = df[col].fillna(df[col].mean())
                elif strategy == "mode":
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        df[col] = df[col].fillna(mode_val[0])

            # --- 3. Transformation Operations ---
            elif op == "clip" and col in df.columns:
                lower = action.metadata.get("min")
                upper = action.metadata.get("max")

                if lower is None or upper is None:
                    # Adaptive clipping using IQR if not specified
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    if lower is None:
                        lower = q1 - 1.5 * iqr
                    if upper is None:
                        upper = q3 + 1.5 * iqr

                df[col] = df[col].clip(lower=lower, upper=upper)

            elif op == "log_transform" and col in df.columns:
                # Add small constant to handle zeros
                df[col] = np.log1p(df[col].clip(lower=0))

            elif op == "group_rare" and col in df.columns:
                threshold = action.metadata.get("threshold", 0.01)
                counts = df[col].value_counts(normalize=True)
                rare_cats = counts[counts < threshold].index
                if not rare_cats.empty:
                    df[col] = df[col].replace(rare_cats, "OTHER")

            elif op == "cast_type" and col in df.columns:
                target_type = action.metadata.get("target_type")
                df[col] = (
                    pd.to_numeric(df[col], errors="coerce")
                    if target_type == "numeric"
                    else df[col].astype(object)
                )

            # --- 5. ML-specific Operations ---
            elif op == "mask_pii" and col in df.columns:
                # Simple masking: replace with [MASKED_TYPE]
                pii_type = action.metadata.get("pii_type", "SENSITIVE")
                # Using loc to ensure we set the values of the series correctly
                df[col] = f"[MASKED_{pii_type.upper()}]"

            elif op == "remove_anomalies":
                # If the detector provided a list of anomalous indices
                indices = action.metadata.get("indices")
                if indices:
                    # Drop by index, handle cases where indices might not exist anymore
                    existing_indices = [idx for idx in indices if idx in df.index]
                    if existing_indices:
                        df = df.drop(index=existing_indices)
                    elif tracer:
                        tracer.trace(
                            "REMEDIATION_SKIPPED",
                            {
                                "reason": "Indices not found in current DF",
                                "operation": op,
                            },
                        )
                elif tracer:
                    tracer.trace(
                        "REMEDIATION_SKIPPED",
                        {"reason": "No indices provided in metadata", "operation": op},
                    )

            # --- 6. Augmentation Operations ---
            elif op == "flag_nulls" and col in df.columns:
                df[f"{col}_is_dirty"] = df[col].isna().astype(int)

            elif (
                col
                and col not in df.columns
                and op != "remove_duplicates"
                and op != "remove_anomalies"
            ):
                if tracer:
                    tracer.trace(
                        "REMEDIATION_SKIPPED",
                        {"reason": f"Column {col} not found", "operation": op},
                    )

        except Exception as e:
            if tracer:
                tracer.trace("REMEDIATION_ERROR", {"error": str(e), "operation": op})

        return df

    def _build_advisory(self, plan: ActionPlan) -> str:
        return " | ".join(f"[{a.action_type}] {a.reason}" for a in plan.actions)
