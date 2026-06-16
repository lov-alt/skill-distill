"""JSON output formatter for programmatic consumption and piping."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console

from skill_distill.models import DiffResult, LintResult


def print_lint_json(result: LintResult, console: Console, indent: int = 2) -> None:
    """Output lint results as JSON to stdout."""
    payload: dict[str, Any] = {
        "skills_checked": result.skills_checked,
        "errors": len(result.errors),
        "warnings": len(result.warnings),
        "info": len(result.info),
        "issues": [
            {
                "rule": i.rule.value,
                "severity": i.severity.value,
                "skill": i.skill_name,
                "message": i.message,
                "suggestion": i.suggestion,
            }
            for i in result.issues
        ],
    }
    console.print(json.dumps(payload, indent=indent, ensure_ascii=False))


def print_diff_json(result: DiffResult, console: Console, indent: int = 2) -> None:
    """Output diff results as JSON to stdout."""
    payload: dict[str, Any] = {
        "skills_compared": result.skills_compared,
        "pairs_flagged": result.pairs_flagged,
        "threshold": result.threshold,
        "pairs": [
            {
                "skill_a": p.skill_a,
                "skill_b": p.skill_b,
                "cosine_similarity": p.cosine_similarity,
                "jaccard_overlap": p.jaccard_overlap,
                "shared_terms": p.shared_terms,
                "suggestion": p.suggestion,
            }
            for p in result.pairs
        ],
    }
    console.print(json.dumps(payload, indent=indent, ensure_ascii=False))


def print_optimize_json(result: dict, console: Console, indent: int = 2) -> None:
    """Output optimizer suggestions as JSON."""
    console.print(json.dumps(result, indent=indent, ensure_ascii=False))


def print_benchmark_json(result, console: Console, indent: int = 2) -> None:
    """Output benchmark results as JSON."""
    payload = {
        "hit_at_1": result.hit_at_1,
        "hit_at_5": result.hit_at_5,
        "precision": result.precision,
        "recall": result.recall,
        "total_cases": result.total_cases,
        "passed": result.passed,
        "confusion": result.confusion,
    }
    console.print(json.dumps(payload, indent=indent, ensure_ascii=False))
