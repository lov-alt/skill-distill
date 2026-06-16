"""Rich terminal output for lint, diff, optimize, and bench results.

Each function takes a result model and a Rich Console, and renders
it into a beautiful, scannable terminal display.

All icons use ASCII to ensure cross-platform compatibility (Windows GBK, etc.).
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from skill_distill.models import DiffResult, LintResult

# ASCII-safe icons for cross-platform compatibility
ICON_OK = "[green]OK[/green]"
ICON_ERR = "[red]ERR[/red]"
ICON_WARN = "[yellow]WARN[/yellow]"
ICON_INFO = "[dim]INFO[/dim]"
ICON_TIP = ">>>"
BAR_FILL = "="
BAR_EMPTY = "-"


# ── Lint ──────────────────────────────────────────────────────────────────────


def print_lint_result(result: LintResult, console: Console) -> None:
    """Render lint results as a Rich panel with per-issue details."""

    if not result.issues:
        console.print(
            Panel(
                f"{ICON_OK}  {result.skills_checked} skill(s) checked -- no issues found.",
                title="skill-distill lint",
                border_style="green",
            )
        )
        return

    table = Table(title=None, box=None, padding=(0, 1))
    table.add_column("", style="bold", width=4)
    table.add_column("Rule", style="dim")
    table.add_column("Skill")
    table.add_column("Message")
    table.add_column("Suggestion", style="green")

    for issue in result.issues:
        icon_map = {"error": ICON_ERR, "warning": ICON_WARN, "info": ICON_INFO}
        icon = icon_map.get(issue.severity, "  ")
        style = {"error": "red", "warning": "yellow", "info": "dim"}.get(
            issue.severity, ""
        )
        table.add_row(
            f"[{style}]{icon}[/{style}]",
            f"[{style}]{issue.rule.value}[/{style}]",
            issue.skill_name,
            issue.message,
            issue.suggestion,
        )

    counts = (
        f"[red]{len(result.errors)} errors[/red]  "
        f"[yellow]{len(result.warnings)} warnings[/yellow]  "
        f"[dim]{len(result.info)} info[/dim]"
    )

    console.print(
        Panel(
            table,
            title=f"skill-distill lint -- {result.skills_checked} skill(s) checked",
            subtitle=counts,
            border_style="red" if result.errors else "yellow",
        )
    )

    # Summary callout
    if result.errors:
        console.print(
            f"[yellow]{ICON_TIP} Tip:[/yellow] Run [bold]skill-distill optimize[/bold] for auto-fix suggestions."
        )


# ── Diff ──────────────────────────────────────────────────────────────────────


def print_diff_result(result: DiffResult, console: Console) -> None:
    """Render diff results with a similarity heatmap and pair details."""

    if not result.pairs:
        console.print(
            Panel(
                f"{ICON_OK}  {result.skills_compared} skills compared -- "
                f"no overlapping pairs above threshold {result.threshold:.2f}.",
                title="skill-distill diff",
                border_style="green",
            )
        )
        return

    table = Table(title=None, box=None, padding=(0, 1))
    table.add_column("Skill A", style="bold")
    table.add_column("Skill B", style="bold")
    table.add_column("Cosine", justify="right")
    table.add_column("Jaccard", justify="right")
    table.add_column("Shared Terms", style="dim", max_width=40)
    table.add_column("Suggestion", style="green")

    for pair in result.pairs:
        sim_color = _similarity_color(pair.cosine_similarity)
        table.add_row(
            pair.skill_a,
            pair.skill_b,
            f"[{sim_color}]{pair.cosine_similarity:.3f}[/{sim_color}]",
            f"{pair.jaccard_overlap:.3f}",
            ", ".join(pair.shared_terms[:5]),
            pair.suggestion,
        )

    console.print(
        Panel(
            table,
            title=f"skill-distill diff -- {result.skills_compared} skills, "
            f"{result.pairs_flagged} overlapping pair(s)",
            subtitle=f"Threshold: cosine > {result.threshold:.2f}",
            border_style="red",
        )
    )


# ── Optimize ──────────────────────────────────────────────────────────────────


def print_optimize_result(result: dict, console: Console) -> None:
    """Render optimization suggestions."""
    skills_processed = result.get("skills_processed", 0)
    suggestions = result.get("suggestions", [])

    if not suggestions:
        console.print(
            Panel(
                f"{ICON_OK}  {skills_processed} skill(s) analyzed -- "
                "all descriptions are already sharp.",
                title="skill-distill optimize",
                border_style="green",
            )
        )
        return

    for s in suggestions:
        console.print(
            Panel(
                f"[bold]{s.get('skill', '')}[/bold]\n\n"
                f"[yellow]Current:[/yellow] {s.get('current', '')}\n"
                f"[green]Suggested:[/green] {s.get('suggested', '')}\n\n"
                f"[dim]{s.get('reason', '')}[/dim]",
                border_style="yellow",
            )
        )


# ── Benchmark ─────────────────────────────────────────────────────────────────


def print_benchmark_result(result, console: Console) -> None:
    """Render benchmark metrics in a clean summary table."""
    metrics = Table(title="Routing Accuracy", box=None, padding=(0, 2))
    metrics.add_column("Metric", style="bold")
    metrics.add_column("Score", justify="right")
    metrics.add_column("Bar", width=30)

    for label, value, color in [
        ("Hit@1", result.hit_at_1, _metric_color(result.hit_at_1)),
        ("Hit@5", result.hit_at_5, _metric_color(result.hit_at_5)),
        ("Precision", result.precision, _metric_color(result.precision)),
        ("Recall", result.recall, _metric_color(result.recall)),
    ]:
        bar_width = int(value * 30)
        bar = f"[{color}]{BAR_FILL * bar_width}[/{color}]{BAR_EMPTY * (30 - bar_width)}"
        metrics.add_row(label, f"[{color}]{value:.1%}[/{color}]", bar)

    console.print(
        Panel(
            metrics,
            title="skill-distill bench",
            subtitle=f"{result.total_cases} test cases, {result.passed} passed",
            border_style="blue",
        )
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _similarity_color(value: float) -> str:
    if value > 0.85:
        return "red"
    if value > 0.75:
        return "yellow"
    return "dim"


def _metric_color(value: float) -> str:
    if value >= 0.80:
        return "green"
    if value >= 0.60:
        return "yellow"
    return "red"
