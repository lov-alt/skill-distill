"""Routing accuracy benchmark — evaluates skill routing precision.

Simulates the agent's routing decision: given a natural language query,
which skill description provides the best match?

Uses embedding-based similarity as a proxy for LLM routing behavior.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from skill_distill.models import (
    BenchmarkCase,
    BenchmarkResult,
    BenchmarkSuite,
)
from skill_distill.parser import parse_directory


def run_benchmark(suite_path: Path, skills_dir: Path | None = None) -> BenchmarkResult:
    """Run a benchmark suite against a skills directory.

    Args:
        suite_path: Path to a YAML benchmark file.
        skills_dir: Override for the skills directory in the YAML.

    Returns:
        BenchmarkResult with Hit@K, precision, recall, and confusion matrix.
    """
    suite = _load_suite(suite_path)
    target_dir = skills_dir or suite.skills_dir
    skills = parse_directory(target_dir)

    if not skills:
        return BenchmarkResult(
            hit_at_1=0.0, hit_at_5=0.0,
            precision=0.0, recall=0.0,
            total_cases=len(suite.test_cases),
        )

    # Build name → skill map
    skill_map = {s.name: s for s in skills}

    hit_1 = 0
    hit_5 = 0
    total = len(suite.test_cases)
    confusion: dict[str, dict[str, int]] = {}

    for case in suite.test_cases:
        ranked = _rank_skills(case.query, skills)
        predicted = ranked[0] if ranked else ""

        # Hit@K
        if predicted == case.expected:
            hit_1 += 1
        if case.expected in ranked[:5]:
            hit_5 += 1

        # Confusion matrix
        if case.expected not in confusion:
            confusion[case.expected] = {}
        confusion[case.expected][predicted] = (
            confusion[case.expected].get(predicted, 0) + 1
        )

    # Macro precision / recall
    precision = hit_1 / total if total > 0 else 0.0
    recall = hit_5 / total if total > 0 else 0.0

    return BenchmarkResult(
        hit_at_1=round(precision, 4),
        hit_at_5=round(recall, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        confusion=confusion,
        total_cases=total,
        passed=hit_1,
    )


def _load_suite(path: Path) -> BenchmarkSuite:
    """Load a benchmark suite from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = [
        BenchmarkCase(
            query=c["query"],
            expected=c["expected"],
            acceptable=c.get("acceptable", []),
        )
        for c in data.get("test_cases", [])
    ]
    return BenchmarkSuite(
        skills_dir=Path(data.get("skills_dir", ".")),
        test_cases=cases,
    )


def _rank_skills(query: str, skills: list, top_k: int = 5) -> list[str]:
    """Rank skills by relevance to the query.

    Tries embedding similarity first, falls back to keyword overlap.
    """
    # Try embedding-based ranking
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        import numpy as np

        q_emb = model.encode([query], show_progress_bar=False)[0]
        s_descs = [s.description for s in skills]
        s_embs = model.encode(s_descs, show_progress_bar=False)

        scores = [
            float(np.dot(q_emb, se) / (np.linalg.norm(q_emb) * np.linalg.norm(se)))
            for se in s_embs
        ]
        ranked = sorted(
            zip([s.name for s in skills], scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [name for name, _ in ranked[:top_k]]

    except ImportError:
        pass

    # Fallback: keyword overlap scoring
    query_tokens = set(query.lower().split())
    scored = []
    for skill in skills:
        desc_tokens = set(skill.description.lower().split())
        overlap = len(query_tokens & desc_tokens)
        # Bonus for name match
        name_bonus = 2.0 if skill.name.lower() in query.lower() else 0.0
        scored.append((skill.name, overlap + name_bonus))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in scored[:top_k]]
