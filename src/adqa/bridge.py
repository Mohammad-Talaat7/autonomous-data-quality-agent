# adqa/bridge.py
"""Bridge module for Rust ↔ Python ADQA interop via pyo3.

Stores the last ADQAResult so subsequent calls (explain, remediate, chat, save)
can operate on it without re-serialising everything through pyo3.

Exposed entry points (called from Rust):
    ping()                  -> health check (adqa version, python path)
    run_analysis(cfg)       -> full analysis, stores _last_result
    run_explain()           -> root cause analysis on _last_result
    run_remediation()       -> remediation proposals on _last_result
    run_chat(question)      -> chat session over _last_result
    save_healed(path)       -> write healed dataframe to disk
    preview_data(path)      -> preview a file (shape, columns, dtypes, head)
"""

from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd

from adqa.chat.session import ChatSession
from adqa.config.model import (
    ADQAConfig,
    DetectionConfig,
    DetectionThresholds,
    ExecutionConfig,
    ExecutionMode,
    LLMConfig,
    ProfilingConfig,
    ProfilingThresholds,
    ScoringConfig,
)
from adqa.core.api import ADQA
from adqa.core.result import ADQAResult
from adqa.data_ingress.datasource import DataSource
from adqa.data_ingress.factory import DataReaderFactory
from adqa.explanation.engine import ExplanationEngine
from adqa.explanation.remediation import RemediationProposalEngine
from adqa.explanation.root_cause import RootCauseEngine
from adqa.llm.client import LiteLLMClient

_last_result: ADQAResult | None = None
_last_config: dict[str, Any] | None = None


def _mode(value: str) -> ExecutionMode:
    m = value.lower()
    if m == "automatic":
        return ExecutionMode.AUTOMATIC
    if m == "human":
        return ExecutionMode.HUMAN_IN_LOOP
    return ExecutionMode.ADVISORY


# ── Analysis ──────────────────────────────────────────────────────────


def run_analysis(cfg: dict) -> str:
    """Run a full ADQA analysis. Returns JSON string of result summary."""
    global _last_result, _last_config
    _last_config = cfg

    llm = dict(cfg.get("llm", {}))
    # Default model to gpt-5.4-nano when LLM is enabled but no model specified
    if llm.get("enabled") and not llm.get("model"):
        llm["model"] = "gpt-5.4-nano"
    profiling = cfg.get("profiling", {})
    thresholds = cfg.get("thresholds", {})

    config = ADQAConfig(
        tracing_enabled=cfg.get("tracing_enabled", True),
        lineage_enabled=cfg.get("lineage_enabled", False),
        ml_enabled=cfg.get("ml_enabled", False),
        execution_mode=_mode(cfg.get("mode", "advisory")),
        profiling=ProfilingConfig(
            sample_size=profiling.get("sample_size", 10000),
            rounding_precision=profiling.get("rounding_precision", 4),
            thresholds=ProfilingThresholds(),
        ),
        detection=DetectionConfig(
            thresholds=DetectionThresholds(
                missing_values_threshold=thresholds.get("missing", 0.2),
                constant_column_threshold=thresholds.get("constant", 1.0),
                duplicate_rows_threshold=thresholds.get("duplicate", 0.1),
                imbalance_threshold=thresholds.get("imbalance", 0.9),
                skewness_threshold=thresholds.get("skewness", 1.0),
                correlation_threshold=thresholds.get("correlation", 0.9),
                pattern_match_threshold=thresholds.get("pattern", 0.8),
                outlier_ratio_threshold=thresholds.get("outlier", 0.05),
            ),
        ),
        scoring=ScoringConfig(),
        execution=ExecutionConfig(stop_on_block=cfg.get("stop_on_block", False)),
        llm=LLMConfig(
            enabled=llm.get("enabled", False),
            provider=llm.get("provider", "litellm"),
            model=llm.get("model") or "gpt-5.4-nano",
            temperature=llm.get("temperature", 0.0),
            timeout_seconds=llm.get("timeout_seconds", 30),
            max_input_chars=llm.get("max_input_chars", 12000),
            redact_samples=llm.get("redact_samples", True),
            api_key=llm.get("api_key") or None,
            api_base=llm.get("api_base") or None,
            service_tier=llm.get("service_tier") or None,
        ),
    )

    data_path = cfg.get("data_path", "")
    adqa = ADQA.from_path(data_path, config=config)
    result = adqa.analyze()
    _last_result = result

    return json.dumps(_result_summary(result))


# ── Cost info from litellm ──────────────────────────────────────────────


def get_cost_info(
    provider: str | None = None,
    model_str: str | None = None,
    flex_enabled: bool = False,
) -> str:
    """Return a formatted cost string for the selected model/provider."""
    try:
        import litellm

        model = model_str or "gpt-4o"
        prov = provider or "openai"

        info = litellm.get_model_info(model)
        in_cost = info.get("input_cost_per_token", 0) if isinstance(info, dict) else 0
        out_cost = info.get("output_cost_per_token", 0) if isinstance(info, dict) else 0

        flex_mult = 0.5 if (flex_enabled and "gpt-5" in model.lower()) else 1.0

        in_m = in_cost * 1_000_000 * flex_mult
        out_m = out_cost * 1_000_000 * flex_mult

        flex_note = " (Flex x0.5 discount)" if flex_mult < 1.0 else ""
        return f"{prov} | {model} ${in_m:.2f}/1MTok | ${out_m:.2f}/1MTok{flex_note}"
    except Exception:
        return "Cost: N/A"


def ping() -> str:
    """Lightweight health check used by the Rust UI at startup.

    Returns JSON with the adqa package version and a short status string.
    This avoids surfacing the raw 'No module named adqa' message to users
    when the Python environment is mis-configured.
    """
    import sys

    try:
        from importlib.metadata import version

        ver = version("adqa")
    except Exception:
        ver = "unknown"
    return json.dumps(
        {
            "ok": True,
            "version": ver,
            "python": sys.executable,
        }
    )


def _result_summary(result: ADQAResult) -> dict:
    """Build a JSON-safe summary from the ADQAResult."""
    summary: dict[str, Any] = {
        "error": result.error,
        "warnings": result.warnings or [],
        "trace_id": result.trace_id,
        "blocked": result.blocked,
        "execution_mode": result.execution_mode,
    }
    if result.decision:
        summary["decision"] = {
            "decision": result.decision.decision,
            "score": result.decision.score,
            "affected_columns": result.decision.affected_columns,
            "dimension_breakdown": result.decision.dimension_breakdown,
        }
    if result.explanation:
        summary["explanation"] = {
            "short_summary": result.explanation.short_summary,
            "top_issues": result.explanation.top_issues,
            "next_steps": result.explanation.recommended_next_steps,
        }
    if result.detections:
        dets = result.detections
        summary["detections"] = {
            "rule_count": len(dets.detections),
            "ml_count": len(dets.ml_evidence),
        }
    if result.dataframe is not None:
        summary["dataframe"] = {
            "rows": result.dataframe.shape[0],
            "cols": result.dataframe.shape[1],
            "columns": list(result.dataframe.columns),
        }
    return summary


# ── Root cause / Explain ──────────────────────────────────────────────


def run_explain() -> str:
    """Run root cause analysis on the last result. Returns JSON list of causes."""
    global _last_result
    if _last_result is None:
        return json.dumps(
            {"error": "No analysis result available. Run analysis first."}
        )

    if _last_result.detections is None or _last_result.scores is None:
        return json.dumps({"error": "No detections/scores available."})

    try:
        engine = RootCauseEngine()
        profile = (
            getattr(_last_result.profiles, "dataset_profile", None)
            if _last_result.profiles
            else None
        )

        causes = list(
            engine.analyse(
                detections=_last_result.detections,
                scores=_last_result.scores,
                dataset_profile=profile,
            )
        )
        return json.dumps(
            [
                {
                    "cause": c.cause,
                    "confidence": c.confidence,
                    "evidence": list(c.evidence[:3]),
                }
                for c in causes
            ]
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── LLM Explanation (natural language) ──────────────────────────────────


def run_llm_explain(
    api_key: str | None = None,
    api_base: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Generate a natural-language explanation of the analysis using the LLM."""
    global _last_result

    if _last_result is None or _last_result.decision is None:
        return "No analysis result to explain."

    try:
        llm_cfg_dict = (_last_config or {}).get("llm", {})
        provider = provider or llm_cfg_dict.get("provider", "litellm")
        model = model or llm_cfg_dict.get("model") or "gpt-5.4-nano"
        api_key = (
            api_key or os.environ.get("OPENAI_API_KEY") or llm_cfg_dict.get("api_key")
        )
        api_base = (
            api_base
            or os.environ.get("OPENAI_API_BASE")
            or llm_cfg_dict.get("api_base")
        )
        service_tier = llm_cfg_dict.get("service_tier") or None

        import json

        decision_dict = (
            _last_result.decision.to_dict()
            if hasattr(_last_result.decision, "to_dict")
            else str(_last_result.decision)
        )

        prompt = (
            "You are a data quality analyst. Explain the following analysis "
            "result in clear, "
            "plain English that a non-technical user can understand. "
            "Describe what was found, why it matters, and what actions are "
            "recommended.\n\n"
            f"Analysis result:\n{json.dumps(decision_dict, default=str, indent=2)}"
        )

        from .llm.client import LiteLLMClient
        from .llm.models import LLMMessage, LLMRequest

        request = LLMRequest(
            provider=provider,
            model=model,
            prompt_version="explain-v1",
            messages=[LLMMessage(role="user", content=prompt)],
            api_key=api_key,
            api_base=api_base,
            service_tier=service_tier,
            metadata={"task": "explain"},
        )

        client = LiteLLMClient()
        response = client.complete(request)
        return response.content

    except Exception as e:
        return f"LLM explanation failed: {e}"


# ── Remediation ───────────────────────────────────────────────────────


def run_remediation() -> str:
    """Run remediation proposals on the last result. Returns JSON list."""
    global _last_result
    if _last_result is None:
        return json.dumps(
            {"error": "No analysis result available. Run analysis first."}
        )

    if _last_result.decision is None:
        return json.dumps({"error": "No decision available."})

    try:
        engine = RemediationProposalEngine()
        bundle = engine.propose(
            decision=_last_result.decision,
            action_plan=_last_result.plan,
        )
        return json.dumps(
            [
                {
                    "issue_type": p.issue_type,
                    "action": p.operational_mapping or p.proposed_action or "review",
                    "risk_level": p.risk_level,
                    "requires_approval": p.requires_approval,
                }
                for p in bundle.proposals
            ]
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Chat ──────────────────────────────────────────────────────────────

_chat_session = None


def run_chat(
    question: str,
    api_key: str | None = None,
    api_base: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Send a chat question. Returns the reply string."""
    global _last_result, _chat_session

    if _last_result is None:
        return "Run analysis first to enable chat."

    try:
        llm_cfg_dict = (_last_config or {}).get("llm", {})
        new_model = model or llm_cfg_dict.get("model") or "gpt-5.4-nano"
        new_provider = provider or llm_cfg_dict.get("provider") or "litellm"
        # Rebuild session when model or provider changes
        if _chat_session is not None:
            old_model = getattr(_chat_session, "_model", None)
            old_provider = getattr(_chat_session, "_provider", None)
            if old_model != new_model or old_provider != new_provider:
                _chat_session = None
        if _chat_session is None:
            llm_cfg = LLMConfig(
                enabled=llm_cfg_dict.get("enabled", False),
                provider=new_provider,
                model=new_model,
                temperature=llm_cfg_dict.get("temperature", 0.0),
                timeout_seconds=llm_cfg_dict.get("timeout_seconds", 30),
                max_input_chars=llm_cfg_dict.get("max_input_chars", 12000),
                redact_samples=llm_cfg_dict.get("redact_samples", True),
                api_key=api_key or llm_cfg_dict.get("api_key"),
                api_base=api_base or llm_cfg_dict.get("api_base"),
                service_tier=llm_cfg_dict.get("service_tier") or None,
            )
            client = LiteLLMClient()
            expl_engine = ExplanationEngine(client=client, config=llm_cfg)
            rem_engine = RemediationProposalEngine()
            _chat_session = ChatSession(
                client=client,
                model=new_model,
                provider=new_provider,
                explanation_engine=expl_engine,
                remediation_engine=rem_engine,
                result=_last_result,
            )

        return _chat_session.send(question)
    except Exception as e:
        return f"[Chat error] {e}"


# ── Session helpers ───────────────────────────────────────────────────


def reset_chat_session() -> str:
    """Forget the cached ChatSession so the next call rebuilds it.

    Called from the GUI when the user edits the LLM credentials, so the
    freshly-set key/base is picked up by subsequent chat calls.
    """
    global _chat_session
    _chat_session = None
    return json.dumps({"ok": True})


# ── Heal data with LLM ─────────────────────────────────────────────────


def run_heal(
    api_key: str | None = None,
    api_base: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Heal the last result's dataframe using LLM-powered remediation."""
    global _last_result

    if _last_result is None or _last_result.dataframe is None:
        return json.dumps(
            {"error": "No analysis result available. Run analysis first."}
        )

    if _last_result.decision is None or _last_result.plan is None:
        return json.dumps({"error": "No decision/plan available."})

    try:
        from .execution.engine import ExecutionEngine
        from .execution.self_healing import SelfHealingController
        from .explanation.remediation import RemediationProposalEngine

        # 1. Generate remediation proposals
        engine = RemediationProposalEngine()
        bundle = engine.propose(
            decision=_last_result.decision,
            action_plan=_last_result.plan,
        )

        # 2. Build an ActionPlan from proposals that LLM can auto-heal
        from .execution.models import Action, ActionPlan

        actions: list[Action] = []
        for p in bundle.proposals:
            action = SelfHealingController.build_healing_proposal(
                p, _last_result.decision
            )
            if action is not None:
                actions.append(action)

        if not actions:
            return json.dumps(
                {
                    "message": "No auto-healable actions found. Review proposals "
                    "manually.",
                    "preview": _dataframe_preview(_last_result.dataframe),
                }
            )

        plan = ActionPlan(
            summary="LLM-driven auto-healing",
            actions=actions,
            requires_human=False,
            approved=True,
        )

        # 3. Execute the healing actions
        exec_engine = ExecutionEngine()
        _, healed_df = exec_engine.execute_plan(plan, _last_result.dataframe)

        if healed_df is not None:
            _last_result.dataframe = healed_df
            preview = _dataframe_preview(healed_df)
            return json.dumps(
                {
                    "message": f"Healed {len(actions)} issues.",
                    "preview": preview,
                    "path": "",
                }
            )

        return json.dumps(
            {
                "message": "Healing completed but no dataframe returned.",
                "preview": "",
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Save healed ───────────────────────────────────────────────────────


def _dataframe_preview(df: pd.DataFrame) -> str:
    """Return a short text preview of the dataframe."""
    import io

    buf = io.StringIO()
    df.head(20).to_csv(buf, index=False)
    return buf.getvalue()


def save_healed(path: str) -> str:
    """Save the healed dataframe to a CSV. Returns status JSON."""
    global _last_result
    if _last_result is None:
        return json.dumps({"error": "No analysis result available."})

    if _last_result.dataframe is None:
        return json.dumps({"error": "No dataframe in result."})

    try:
        _last_result.dataframe.to_csv(path, index=False)
        return json.dumps(
            {
                "ok": True,
                "path": path,
                "rows": _last_result.dataframe.shape[0],
                "cols": _last_result.dataframe.shape[1],
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Data preview ──────────────────────────────────────────────────────


def preview_data(path: str) -> str:
    """Preview a data file. Returns JSON with shape, columns, dtypes, head."""
    if not path or not path.strip():
        return json.dumps(
            {"error": "No data path provided. Type a file path or pick a sample."}
        )

    resolved = os.path.abspath(os.path.expanduser(path.strip()))
    if not os.path.exists(resolved):
        return json.dumps({"error": f"File not found: {resolved} (cwd: {os.getcwd()})"})

    try:
        source = DataSource.load(resolved)
        reader = DataReaderFactory.create(source)
        df = reader.read()

        # Schema: column, dtype, missing count + percent
        total_rows = max(int(df.shape[0]), 1)
        schema_lines = [
            f"{'Column':<24} {'Type':<14} {'Missing':>8}  {'%':>6}",
            "-" * 56,
        ]
        for c, t in zip(df.columns, df.dtypes, strict=False):
            try:
                miss = int(df[c].isna().sum())
            except Exception:
                miss = 0
            pct = 100.0 * miss / total_rows
            schema_lines.append(
                f"{str(c)[:24]:<24} {str(t)[:14]:<14} {miss:>8d}  {pct:>5.1f}%"
            )
        schema_str = "\n".join(schema_lines)

        # Head: 20 rows with widened display so columns don't wrap unnecessarily
        with pd.option_context(
            "display.max_columns",
            None,
            "display.width",
            240,
            "display.max_colwidth",
            48,
        ):
            head_str = df.head(20).to_string()

        return json.dumps(
            {
                "rows": int(df.shape[0]),
                "cols": int(df.shape[1]),
                "columns": list(df.columns),
                "dtypes": {
                    str(c): str(t) for c, t in zip(df.columns, df.dtypes, strict=False)
                },
                "schema": schema_str,
                "head": head_str,
                "resolved_path": resolved,
            }
        )
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
