"""Semantic overlap detection between skill descriptions.

Uses a two-pronged approach:
  1. Keyword-level Jaccard similarity (always available).
  2. Embedding-based cosine similarity (optional, requires sentence-transformers).

The combination catches both surface-level and deep semantic overlaps.
"""

from __future__ import annotations

import re
from pathlib import Path

from skill_distill.models import DiffPair, DiffResult
from skill_distill.parser import parse_directory


def diff_skills(
    directory: Path,
    threshold: float = 0.75,
) -> DiffResult:
    """Compare all skills in a directory for semantic overlap.

    Args:
        directory: Path containing skill markdown files.
        threshold: Cosine similarity threshold (0.0–1.0) for flagging a pair.

    Returns:
        DiffResult with all flagged overlapping pairs.
    """
    skills = parse_directory(directory)
    if len(skills) < 2:
        return DiffResult(
            skills_compared=len(skills),
            pairs_flagged=0,
            pairs=[],
            threshold=threshold,
        )

    # Compute embeddings if available, else fall back to keyword-only
    embeddings = _compute_embeddings(skills)

    pairs: list[DiffPair] = []
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            a, b = skills[i], skills[j]

            # Jaccard (always computed)
            tokens_a = _tokenize(a.description)
            tokens_b = _tokenize(b.description)
            jaccard = _jaccard(tokens_a, tokens_b)
            shared = sorted(tokens_a & tokens_b)

            # Cosine (only if embeddings available)
            cosine = 0.0
            if embeddings is not None:
                import numpy as np

                ea = embeddings[i]
                eb = embeddings[j]
                cosine = float(np.dot(ea, eb) / (np.linalg.norm(ea) * np.linalg.norm(eb)))

            # Flag if either metric exceeds threshold
            # (Jaccard is harsher, so we scale its effective threshold)
            effective_jaccard_threshold = threshold * 0.4
            if cosine > threshold or jaccard > effective_jaccard_threshold:
                pairs.append(
                    DiffPair(
                        skill_a=a.name,
                        skill_b=b.name,
                        cosine_similarity=round(cosine, 4),
                        jaccard_overlap=round(jaccard, 4),
                        shared_terms=shared,
                        suggestion=_build_suggestion(a.name, b.name, shared),
                    )
                )

    return DiffResult(
        skills_compared=len(skills),
        pairs_flagged=len(pairs),
        pairs=sorted(pairs, key=lambda p: p.cosine_similarity, reverse=True),
        threshold=threshold,
    )


# ── Embedding helpers ─────────────────────────────────────────────────────────


def _compute_embeddings(skills: list) -> list | None:
    """Try to compute sentence embeddings. Returns None if not available."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None

    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    descriptions = [s.description for s in skills]
    return model.encode(descriptions, show_progress_bar=False)


# ── Text helpers ──────────────────────────────────────────────────────────────


def _tokenize(text: str) -> set[str]:
    """Tokenize text into a set of meaningful lowercase tokens."""
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    # Filter common stopwords
    stopwords = {
        "the", "and", "for", "use", "with", "that", "this",
        "from", "when", "your", "can", "not", "are", "its",
    }
    return {t for t in tokens if t not in stopwords}


def _jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return len(set_a & set_b) / union


def _build_suggestion(name_a: str, name_b: str, shared: list[str]) -> str:
    """Generate a concrete suggestion for resolving overlap."""
    if not shared:
        return "Consider making descriptions more domain-specific."
    terms = ", ".join(shared[:5])
    return (
        f"Shared terms ({terms}) create ambiguity. "
        f"Add distinct trigger phrases to '{name_a}' and '{name_b}' "
        f"so the agent can tell them apart."
    )
