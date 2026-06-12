# adqa/cli.py
import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from adqa.config.model import ADQAConfig
from adqa.core.api import ADQA

console = Console()


def build_config(args: argparse.Namespace) -> ADQAConfig:
    profiling_thresholds = {
        "semantic_min_confidence": args.semantic_min_confidence,
        "anomaly_contamination": args.anomaly_contamination,
        "anomaly_n_estimators": args.anomaly_n_estimators,
    }

    detection_thresholds = {
        "missing_values_threshold": args.missing_threshold,
        "outlier_ratio_threshold": args.outlier_threshold,
        "constant_column_threshold": args.constant_threshold,
        "duplicate_rows_threshold": args.duplicate_threshold,
        "imbalance_threshold": args.imbalance_threshold,
        "skewness_threshold": args.skewness_threshold,
        "correlation_threshold": args.correlation_threshold,
        "pattern_match_threshold": args.pattern_threshold,
    }

    base = ADQAConfig.from_cli_args(
        mode=args.mode,
        tracing_enabled=not args.no_trace,
        ml_enabled=not args.no_ml,
        lineage_enabled=not args.no_trace and not args.no_lineage,
        prof_ml_enabled=not args.no_prof_ml,
        sample_size=args.sample_size,
        rounding_precision=args.rounding_precision,
        profiling_thresholds=profiling_thresholds,
        detection_thresholds=detection_thresholds,
        stop_on_block=args.stop_on_block,
    ).model_dump()

    # Remove llm key from base dict to avoid kwarg conflict below
    base.pop("llm", None)

    return ADQAConfig(
        **base,
        llm={
            "enabled": args.command == "explain" or args.llm_enabled,
            "provider": args.llm_provider,
            "model": args.llm_model,
            "temperature": args.llm_temperature,
            "timeout_seconds": args.llm_timeout_seconds,
            "max_input_chars": args.llm_max_input_chars,
            "redact_samples": not args.no_llm_redaction,
        },
    )


def render_result(result: object, *, require_explanation: bool) -> int:
    summary = result.summary()
    console.print(Panel(summary, title="[bold]Analysis Result[/bold]", expand=False))

    if result.error:
        console.print(f"[bold red]Error:[/bold red] {result.error}")
        return 1

    if result.warnings:
        for warning in result.warnings:
            console.print(f"[bold yellow]Warning:[/bold yellow] {warning}")

    if result.detections and (
        result.detections.detections or result.detections.ml_evidence
    ):
        table = Table(title="Detections Summary")
        table.add_column("Type", style="cyan")
        table.add_column("Column", style="magenta")
        table.add_column("Score/Severity", justify="right")

        for detection in result.detections.detections:
            table.add_row(
                detection.issue_type,
                detection.column or "DATASET",
                f"{detection.severity_hint:.2f}",
            )

        for evidence in result.detections.ml_evidence:
            table.add_row(f"ML: {evidence.signal_type}", "DATASET", f"{evidence.score:.2f}")

        console.print(table)

    if result.explanation:
        explanation = result.explanation
        body = "\n".join(
            [
                explanation.short_summary,
                "",
                f"Top issues: {', '.join(explanation.top_issues) or 'n/a'}",
                f"Affected columns: {', '.join(explanation.affected_columns) or 'n/a'}",
                f"Why: {'; '.join(explanation.why_decision) or 'n/a'}",
                f"Next steps: {'; '.join(explanation.recommended_next_steps) or 'n/a'}",
                f"Uncertainty: {explanation.uncertainty or 'n/a'}",
            ]
        )
        console.print(Panel(body, title="[bold]LLM Explanation[/bold]", expand=False))
    elif require_explanation:
        console.print("[bold red]Error:[/bold red] No explanation was produced.")
        return 1

    if result.actions:
        console.print("\n[bold]Executed Actions:[/bold]")
        for action in result.actions:
            console.print(f"- [[bold]{action.action_type}[/bold]] {action.reason}")

    if result.blocked:
        console.print(
            "\n[bold red]Pipeline BLOCKED[/bold red] due to critical quality issues."
        )
    elif result.approval_payload:
        console.print(
            "\n[bold yellow]PENDING APPROVAL[/bold yellow]: Human review required."
        )

    return 0


def run_analysis_command(
    args: argparse.Namespace,
    *,
    require_explanation: bool = False,
) -> int:
    try:
        config = build_config(args)

        console.print("[bold blue]ADQA Analysis Initiated[/bold blue]")
        console.print(f"Source: [green]{args.path}[/green]")
        console.print(f"Mode: [yellow]{args.mode}[/yellow]\n")

        if config.llm.enabled:
            console.print(
                "[bold yellow]LLM Enabled: Don't use any sensitive information, as the data may be sent to the LLM provider you are using.[/bold yellow]"
            )

        adqa = ADQA.from_path(args.path, config=config)

        with console.status("[bold green]Analyzing data..."):
            result = adqa.analyze()

        status = render_result(result, require_explanation=require_explanation)

        if args.output and result.dataframe is not None:
            result.dataframe.to_csv(args.output, index=False)
            console.print(
                f"\n[bold green]Remediated data saved to:[/bold green] {args.output}"
            )

        return status
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        import traceback

        if args.verbose:
            traceback.print_exc()
        return 1


def run_analyze(args: argparse.Namespace) -> int:
    return run_analysis_command(args, require_explanation=False)


def run_explain(args: argparse.Namespace) -> int:
    if args.mode == "chat":
        return run_explain_chat(args)
    return run_analysis_command(args, require_explanation=True)


def add_analysis_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="Path to the data source (local or remote)")
    parser.add_argument(
        "--mode",
        choices=["advisory", "automatic", "human"],
        default="advisory",
        help="Execution mode",
    )
    parser.add_argument("--output", "-o", help="Path to save remediated data")
    parser.add_argument("--no-trace", action="store_true", help="Disable tracing")
    parser.add_argument("--no-ml", action="store_true", help="Disable ML features")
    parser.add_argument(
        "--no-lineage", action="store_true", help="Disable data lineage"
    )
    parser.add_argument(
        "--no-prof-ml", action="store_true", help="Disable ML profiling"
    )
    parser.add_argument(
        "--stop-on-block",
        action="store_true",
        default=True,
        help="Stop on first block action",
    )

    parser.add_argument(
        "--sample-size", type=int, default=10000, help="Profiling sample size"
    )
    parser.add_argument(
        "--rounding-precision",
        type=int,
        default=4,
        help="Rounding precision for results",
    )

    parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.2,
        help="Threshold for missing values",
    )
    parser.add_argument(
        "--outlier-threshold",
        type=float,
        default=0.05,
        help="Threshold for outlier ratio",
    )
    parser.add_argument(
        "--constant-threshold",
        type=float,
        default=1.0,
        help="Threshold for constant columns",
    )
    parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.1,
        help="Threshold for duplicate rows",
    )
    parser.add_argument(
        "--imbalance-threshold",
        type=float,
        default=0.9,
        help="Threshold for category imbalance",
    )
    parser.add_argument(
        "--skewness-threshold", type=float, default=1.0, help="Threshold for skewness"
    )
    parser.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.9,
        help="Threshold for high correlation",
    )
    parser.add_argument(
        "--pattern-threshold",
        type=float,
        default=0.8,
        help="Threshold for pattern match",
    )

    parser.add_argument(
        "--semantic-min-confidence",
        type=float,
        default=0.4,
        help="Min confidence for semantic classifier",
    )
    parser.add_argument(
        "--anomaly-contamination",
        type=float,
        default=0.05,
        help="Isolation Forest contamination",
    )
    parser.add_argument(
        "--anomaly-n-estimators",
        type=int,
        default=50,
        help="Number of estimators for Isolation Forest",
    )

    parser.add_argument(
        "--llm-enabled",
        action="store_true",
        default=False,
        help="Enable LLM explanations during analysis",
    )
    parser.add_argument(
        "--llm-provider",
        default="litellm",
        help="LLM provider adapter to use",
    )
    parser.add_argument(
        "--llm-model",
        help="Model name to use when LLM explanations are enabled",
    )
    parser.add_argument(
        "--llm-temperature",
        type=float,
        default=0.0,
        help="LLM temperature, kept low for deterministic explanations",
    )
    parser.add_argument(
        "--llm-timeout-seconds",
        type=int,
        default=30,
        help="LLM request timeout in seconds",
    )
    parser.add_argument(
        "--llm-max-input-chars",
        type=int,
        default=12000,
        help="Maximum structured prompt payload size",
    )
    parser.add_argument(
        "--no-llm-redaction",
        action="store_true",
        help="Disable prompt redaction safeguards",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose errors"
    )
def run_explain_chat(args: argparse.Namespace) -> int:
    """Run analysis then launch interactive chat for explain --mode chat."""
    try:
        config = build_config(args)

        console.print("[bold blue]ADQA Analysis + Chat[/bold blue]")
        console.print(f"Source: [green]{args.path}[/green]")
        console.print(f"Mode: [yellow]chat[/yellow]")

        if config.llm.enabled:
            console.print(
                "[bold yellow]LLM Enabled: Don't use any sensitive information,"
                "as the data may be sent to the LLM provider you are using.[/bold yellow]"
            )

        adqa = ADQA.from_path(args.path, config=config)

        with console.status("[bold green]Analyzing data..."):
            result = adqa.analyze()

        status = render_result(result, require_explanation=True)
        if status != 0:
            return status

        from adqa.chat.session import ChatSession
        from adqa.llm.client import LiteLLMClient

        # Build engines for the chat session
        explanation_engine = None
        remediation_engine = None
        if config.llm.enabled:
            from adqa.explanation.engine import ExplanationEngine
            from adqa.explanation.remediation import RemediationProposalEngine

            client = LiteLLMClient()
            explanation_engine = ExplanationEngine(client=client, config=config.llm)
            remediation_engine = RemediationProposalEngine()

        chat_client = LiteLLMClient()
        session = ChatSession(
            client=chat_client,
            explanation_engine=explanation_engine,
            remediation_engine=remediation_engine,
            result=result,
        )

        console.print(
            "\n[bold]Chat started. Type 'exit' to quit, 'help' for commands.[/bold]"
        )

        while True:
            try:
                user_input = console.input("\n[bold cyan]ADQA > [/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Chat ended.[/dim]")
                break

            user_input = user_input.strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                console.print("[dim]Chat ended.[/dim]")
                break
            if user_input.lower() == "help":
                console.print(
                    "Commands: exit/quit, help, summary, issues, "
                    "columns, explain, fix/remediate, why/cause\n"
                    "Ask any question about the data quality results."
                )
                continue
            if user_input.lower() == "summary":
                console.print(result.summary())
                continue

            response = session.send(user_input)
            console.print(f"[bold green]ADQA:[/bold green] {response}")

        return 0
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1



def run_chat(args: argparse.Namespace) -> int:
    """Run interactive chat session against a completed analysis."""
    try:
        # Force LLM on for chat command
        args.llm_enabled = True
        if not args.llm_model:
            console.print(
                "[bold red]Error: chat requires --llm-model[/bold red]"
            )
            return 1

        config = build_config(args)

        console.print("[bold blue]ADQA Chat Session[/bold blue]")
        console.print(f"Source: [green]{args.path}[/green]")
        console.print(f"Mode: [yellow]{args.mode}[/yellow]")

        console.print(
            "[bold yellow]LLM Enabled: Don't use any sensitive information,"
            "as the data may be sent to the LLM provider you are using.[/bold yellow]"
        )

        adqa = ADQA.from_path(args.path, config=config)

        with console.status("[bold green]Analyzing data..."):
            result = adqa.analyze()

        status = render_result(result, require_explanation=False)
        if status != 0:
            return status

        from adqa.chat.session import ChatSession
        from adqa.llm.client import LiteLLMClient

        client = LiteLLMClient()
        session = ChatSession(client=client, model=config.llm.model or "", result=result)
        session.inject_result(result)

        console.print(
            "\n[bold]Chat started. Type 'exit' to quit, 'help' for commands.[/bold]"
        )

        while True:
            try:
                user_input = console.input("\n[bold cyan]ADQA > [/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Chat ended.[/dim]")
                break

            user_input = user_input.strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                console.print("[dim]Chat ended.[/dim]")
                break
            if user_input.lower() == "help":
                console.print(
                    "Commands: exit/quit, help, summary, issues, "
                    "columns, explain, propose\n"
                    "Ask any question about the data quality results."
                )
                continue
            if user_input.lower() == "summary":
                console.print(result.summary())
                continue
            if user_input.lower() == "explain":
                if result.explanation:
                    console.print(Panel(
                        result.explanation.short_summary,
                        title="[bold]LLM Explanation[/bold]",
                        expand=False,
                    ))
                else:
                    console.print("[dim]No explanation available.[/dim]")
                continue

            response = session.send(user_input)
            console.print(f"[bold green]ADQA:[/bold green] {response}")

        return 0
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1



def main() -> None:
    parser = argparse.ArgumentParser(
        prog="adqa", description="Autonomous Data Quality Agent CLI"
    )
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a data source")
    add_analysis_arguments(analyze_parser)

    # Chat command
    chat_parser = subparsers.add_parser(
        "chat",
        help="Interactive chat session about a data quality analysis",
    )
    add_analysis_arguments(chat_parser)

    explain_parser = subparsers.add_parser(
        "explain",
        help="Analyze a data source and request an LLM explanation",
    )
    add_analysis_arguments(explain_parser)

    args = parser.parse_args()

    if args.version:
        # Assuming version is handled by poetry-dynamic-versioning
        # For now, we can try to get it from importlib.metadata
        try:
            from importlib.metadata import version

            console.print(f"ADQA version: {version('adqa')}")
        except Exception:
            console.print("ADQA version: unknown (dev)")
        return

    if args.command == "analyze":
        sys.exit(run_analyze(args))
    elif args.command == "explain":
        sys.exit(run_explain(args))
    elif args.command == "chat":
        sys.exit(run_chat(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
