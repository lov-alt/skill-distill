"""CLI entry point — the `skill-distill` command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from skill_distill import __version__

app = typer.Typer(
    name="skill-distill",
    help="Sharpen AI agent skills — lint, diff, optimize, and benchmark skill descriptions.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _resolve_path(path: str) -> Path:
    """Resolve and validate a file or directory path."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        console.print(f"[red]Error:[/red] path does not exist — [bold]{p}[/bold]")
        raise typer.Exit(code=1)
    return p


def _use_json(fmt: str) -> bool:
    return fmt.lower() == "json"


# ── lint ──────────────────────────────────────────────────────────────────────


@app.command()
def lint(
    path: Annotated[
        str,
        typer.Argument(help="Path to a skill file or directory of skills."),
    ],
    strict: Annotated[
        bool,
        typer.Option("--strict", "-s", help="Exit with error code if any warnings found."),
    ] = False,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output: 'terminal' (default) or 'json'."),
    ] = "terminal",
) -> None:
    """Check skill descriptions for quality issues."""
    from skill_distill.linter import lint_skills
    from skill_distill.reporter.json import print_lint_json
    from skill_distill.reporter.terminal import print_lint_result

    target = _resolve_path(path)
    result = lint_skills(target)

    if _use_json(fmt):
        print_lint_json(result, console)
    else:
        print_lint_result(result, console)

    exit_code = 1 if (result.errors) or (strict and result.warnings) else 0
    raise typer.Exit(code=exit_code)


# ── diff ──────────────────────────────────────────────────────────────────────


@app.command()
def diff(
    directory: Annotated[
        str,
        typer.Argument(help="Directory containing skill files to compare."),
    ],
    threshold: Annotated[
        float,
        typer.Option("--threshold", "-t", min=0.0, max=1.0,
                     help="Cosine similarity threshold for flagging overlaps."),
    ] = 0.75,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output: 'terminal' (default) or 'json'."),
    ] = "terminal",
) -> None:
    """Find skills with overlapping descriptions."""
    from skill_distill.differ import diff_skills
    from skill_distill.reporter.json import print_diff_json
    from skill_distill.reporter.terminal import print_diff_result

    target = _resolve_path(directory)
    result = diff_skills(target, threshold=threshold)

    if _use_json(fmt):
        print_diff_json(result, console)
    else:
        print_diff_result(result, console)
        if result.pairs_flagged > 0:
            console.print(
                f"\n[yellow]{result.pairs_flagged} overlapping pair(s) found.[/yellow] "
                f"Run [bold]skill-distill optimize[/bold] for suggestions."
            )


# ── optimize ──────────────────────────────────────────────────────────────────


@app.command()
def optimize(
    path: Annotated[
        str,
        typer.Argument(help="Path to a skill file or directory."),
    ],
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Write optimization suggestions back to skill files."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would change without writing files."),
    ] = True,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output: 'terminal' (default) or 'json'."),
    ] = "terminal",
) -> None:
    """Suggest improvements for skill descriptions."""
    from skill_distill.optimizer import optimize_skills
    from skill_distill.reporter.json import print_optimize_json
    from skill_distill.reporter.terminal import print_optimize_result

    target = _resolve_path(path)
    result = optimize_skills(target, apply_changes=apply_changes, dry_run=dry_run)

    if _use_json(fmt):
        print_optimize_json(result, console)
    else:
        print_optimize_result(result, console)


# ── bench ─────────────────────────────────────────────────────────────────────


@app.command()
def bench(
    test_file: Annotated[
        str,
        typer.Argument(help="Path to a benchmark YAML file."),
    ],
    skills: Annotated[
        Optional[str],
        typer.Option("--skills", "-s", help="Skills directory (overrides YAML setting)."),
    ] = None,
    output: Annotated[
        Optional[str],
        typer.Option("--output", "-o", help="Save benchmark results to a JSON file."),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output: 'terminal' (default) or 'json'."),
    ] = "terminal",
) -> None:
    """Benchmark routing accuracy with a test suite."""
    from skill_distill.benchmark import run_benchmark
    from skill_distill.reporter.json import print_benchmark_json
    from skill_distill.reporter.terminal import print_benchmark_result

    suite_path = _resolve_path(test_file)
    skills_dir = _resolve_path(skills) if skills else None
    result = run_benchmark(suite_path, skills_dir=skills_dir)

    if _use_json(fmt):
        print_benchmark_json(result, console)
    else:
        print_benchmark_result(result, console)

    if output:
        output_path = Path(output)
        output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"\n[dim]Results saved to [bold]{output_path}[/bold][/dim]")


# ── init ──────────────────────────────────────────────────────────────────────


@app.command()
def init(
    directory: Annotated[
        str,
        typer.Argument(help="Directory to initialize (defaults to current directory)."),
    ] = ".",
) -> None:
    """Create a .skill-distill.yaml config file."""
    import yaml

    config = {
        "version": 1,
        "rules": {
            "min-length": {"enabled": True, "min_chars": 50},
            "max-length": {"enabled": True, "max_chars": 500},
            "no-triggers": {"enabled": True},
            "vague-terms": {"enabled": True},
            "missing-scope": {"enabled": True},
            "no-negative": {"enabled": False},
        },
        "differ": {"threshold": 0.75},
    }

    config_path = _resolve_path(directory) / ".skill-distill.yaml"
    if config_path.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {config_path}")
        raise typer.Exit(code=0)

    config_path.write_text(yaml.dump(config, default_flow_style=False, indent=2))
    console.print(f"[green]Created[/green] [bold]{config_path}[/bold]")


@app.command()
def version() -> None:
    """Show the current version."""
    console.print(f"[bold]skill-distill[/bold] v{__version__}")


if __name__ == "__main__":
    app()
