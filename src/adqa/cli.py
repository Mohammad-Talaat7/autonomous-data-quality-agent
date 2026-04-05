import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from adqa.config.model import ADQAConfig
from adqa.core.api import ADQA

console = Console()


def run_analyze(args: argparse.Namespace) -> int:
    """
    Run the ADQA analyze command.
    """
    try:
        # Construct threshold objects for nested configs
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

        config = ADQAConfig.from_cli_args(
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
        )

        console.print("[bold blue]ADQA Analysis Initiated[/bold blue]")
        console.print(f"Source: [green]{args.path}[/green]")
        console.print(f"Mode: [yellow]{args.mode}[/yellow]\n")

        # Initialize ADQA
        adqa = ADQA.from_path(args.path, config=config)

        # Run analysis
        with console.status("[bold green]Analyzing data..."):
            result = adqa.analyze()

        # Display Summary
        summary = result.summary()
        console.print(
            Panel(summary, title="[bold]Analysis Result[/bold]", expand=False)
        )

        if result.error:
            console.print(f"[bold red]Error:[/bold red] {result.error}")
            return 1

        # Display detections if any
        if result.detections and (
            result.detections.detections or result.detections.ml_evidence
        ):
            table = Table(title="Detections Summary")
            table.add_column("Type", style="cyan")
            table.add_column("Column", style="magenta")
            table.add_column("Score/Severity", justify="right")

            for d in result.detections.detections:
                table.add_row(
                    d.issue_type, d.column or "DATASET", f"{d.severity_hint:.2f}"
                )

            for m in result.detections.ml_evidence:
                table.add_row(f"ML: {m.signal_type}", "DATASET", f"{m.score:.2f}")

            console.print(table)

        # Actions
        if result.actions:
            console.print("\n[bold]Executed Actions:[/bold]")
            for action in result.actions:
                console.print(f"- [[bold]{action.action_type}[/bold]] {action.reason}")

        if result.blocked:
            console.print(
                "\n[bold red]Pipeline BLOCKED[/bold red] due to "
                "critical quality issues."
            )
        elif result.approval_payload:
            console.print(
                "\n[bold yellow]PENDING APPROVAL[/bold yellow]: Human review required."
            )

        if args.output and result.dataframe is not None:
            result.dataframe.to_csv(args.output, index=False)
            console.print(
                f"\n[bold green]Remediated data saved to:[/bold green] {args.output}"
            )

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
    analyze_parser.add_argument(
        "path", help="Path to the data source (local or remote)"
    )
    analyze_parser.add_argument(
        "--mode",
        choices=["advisory", "automatic", "human_in_loop"],
        default="advisory",
        help="Execution mode",
    )
    analyze_parser.add_argument("--output", "-o", help="Path to save remediated data")
    analyze_parser.add_argument(
        "--no-trace", action="store_true", help="Disable tracing"
    )
    analyze_parser.add_argument(
        "--no-ml", action="store_true", help="Disable ML features"
    )
    analyze_parser.add_argument(
        "--no-lineage", action="store_true", help="Disable data lineage"
    )
    analyze_parser.add_argument(
        "--no-prof-ml", action="store_true", help="Disable ML profiling"
    )
    analyze_parser.add_argument(
        "--stop-on-block",
        action="store_true",
        default=True,
        help="Stop on first block action",
    )

    # Profiling Parameters
    analyze_parser.add_argument(
        "--sample-size", type=int, default=10000, help="Profiling sample size"
    )
    analyze_parser.add_argument(
        "--rounding-precision",
        type=int,
        default=4,
        help="Rounding precision for results",
    )

    # Detection Thresholds
    analyze_parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.2,
        help="Threshold for missing values",
    )
    analyze_parser.add_argument(
        "--outlier-threshold",
        type=float,
        default=0.05,
        help="Threshold for outlier ratio",
    )
    analyze_parser.add_argument(
        "--constant-threshold",
        type=float,
        default=1.0,
        help="Threshold for constant columns",
    )
    analyze_parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.1,
        help="Threshold for duplicate rows",
    )
    analyze_parser.add_argument(
        "--imbalance-threshold",
        type=float,
        default=0.9,
        help="Threshold for category imbalance",
    )
    analyze_parser.add_argument(
        "--skewness-threshold", type=float, default=1.0, help="Threshold for skewness"
    )
    analyze_parser.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.9,
        help="Threshold for high correlation",
    )
    analyze_parser.add_argument(
        "--pattern-threshold",
        type=float,
        default=0.8,
        help="Threshold for pattern match",
    )

    # ML Parameters
    analyze_parser.add_argument(
        "--semantic-min-confidence",
        type=float,
        default=0.4,
        help="Min confidence for semantic classifier",
    )
    analyze_parser.add_argument(
        "--anomaly-contamination",
        type=float,
        default=0.05,
        help="Isolation Forest contamination",
    )
    analyze_parser.add_argument(
        "--anomaly-n-estimators",
        type=int,
        default=50,
        help="Number of estimators for Isolation Forest",
    )

    analyze_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose errors"
    )

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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
