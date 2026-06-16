"""Description optimizer — suggests improvements for better routing distinguishability.

Inspired by the SkillReducer paper's adversarial delta debugging approach:
  1. Decompose description into semantic clauses.
  2. Score each clause for distinguishability contribution.
  3. Flag clauses that dilute the signal (too generic).
  4. Suggest additions: trigger phrases, scope constraints, negative examples.
"""

from __future__ import annotations

import re
from pathlib import Path

from skill_distill.models import VAGUE_WORDS
from skill_distill.parser import parse_directory, parse_file


def optimize_skills(
    target: Path,
    apply_changes: bool = False,
    dry_run: bool = True,
) -> dict:
    """Analyze skills and generate optimization suggestions.

    Args:
        target: File or directory of skills to optimize.
        apply_changes: If True, write suggestions back to files.
        dry_run: If True, don't write (overrides apply_changes).

    Returns:
        Dict with skills_processed, suggestions, and changes_applied.
    """
    if target.is_file():
        skills = [s for s in [parse_file(target)] if s is not None]
    else:
        skills = parse_directory(target)

    suggestions: list[dict] = []

    for skill in skills:
        clauses = _decompose(skill.description)
        scores = _score_clauses(clauses)

        weak_clauses = [c for c, s in zip(clauses, scores) if s < 0.3]
        missing = _check_missing(skill)

        if weak_clauses or missing:
            suggested = _build_improved(skill.description, weak_clauses, missing)
            suggestions.append({
                "skill": skill.name,
                "path": str(skill.path) if skill.path else "",
                "current": skill.description,
                "suggested": suggested,
                "weak_clauses": weak_clauses,
                "missing": missing,
                "reason": _build_reason(weak_clauses, missing),
            })

    changes_applied = 0
    if apply_changes and not dry_run:
        for s in suggestions:
            if s.get("path"):
                _apply_suggestion(s["path"], s["suggested"])
                changes_applied += 1

    return {
        "skills_processed": len(skills),
        "suggestions": suggestions,
        "changes_applied": changes_applied,
    }


# ── Clause analysis ───────────────────────────────────────────────────────────


def _decompose(description: str) -> list[str]:
    """Split description into semantic clauses."""
    clauses = re.split(r"[.;；。；\n—–-]+", description)
    result: list[str] = []
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        if len(clause) > 80 and "," in clause:
            sub = [s.strip() for s in clause.split(",") if s.strip()]
            if len(sub) > 1:
                result.extend(sub)
                continue
        result.append(clause)
    return result


def _score_clauses(clauses: list[str]) -> list[float]:
    """Score each clause by distinguishability contribution (0.0–1.0).

    High score -> helps the agent route correctly.
    Low score -> generic noise that creates ambiguity.
    """
    scores: list[float] = []
    for clause in clauses:
        score = 0.5

        # Boost: specific nouns, domain terms
        specific = len(re.findall(r"\b[A-Z][a-z]+\b|\b[a-z]{6,}\b", clause))
        score += min(0.3, specific * 0.05)

        # Boost: trigger-like phrasing
        if re.search(r"\b(use|when|for|trigger|invoke)\b", clause, re.IGNORECASE):
            score += 0.15

        # Boost: scope-defining language
        if re.search(r"\b(only|specifically|particularly|exclusively)\b", clause, re.IGNORECASE):
            score += 0.1

        # Penalize: vague words
        words = set(re.findall(r"\b\w+\b", clause.lower()))
        vague_count = len(words & VAGUE_WORDS)
        score -= min(0.3, vague_count * 0.1)

        # Penalize: very short clauses
        if len(clause.split()) < 3:
            score -= 0.15

        scores.append(max(0.0, min(1.0, score)))

    return scores


def _check_missing(skill) -> list[str]:
    """Check for critical missing elements in a description."""
    missing: list[str] = []
    desc = skill.description.lower()

    if not re.search(r"\b(use|when|for|适用于|用于)\b", desc):
        missing.append("trigger phrase (e.g. 'Use when the user asks for...')")

    if not re.search(r"\b(not|don't|avoid|不要|避免)\b", desc):
        missing.append("negative constraint (when NOT to invoke)")

    if len(skill.description) < 50:
        missing.append("minimum length (50+ chars recommended)")

    return missing


# ── Suggestion builder ────────────────────────────────────────────────────────


def _build_improved(
    current: str,
    weak_clauses: list[str],
    missing: list[str],
) -> str:
    """Build improved description by removing weak clauses, adding missing elements."""
    parts = [c for c in _decompose(current) if c not in weak_clauses]
    improved = " ".join(parts).strip()

    if "trigger phrase" in str(missing):
        improved += " Use when the task involves [specific domain or action]."
    if "negative constraint" in str(missing):
        improved += " Not for [opposite or simpler alternative]."

    return improved


def _build_reason(weak_clauses: list[str], missing: list[str]) -> str:
    """Human-readable explanation for the suggestion."""
    reasons: list[str] = []
    if weak_clauses:
        reasons.append(
            f"Removed {len(weak_clauses)} generic clause(s) "
            f"that don't help distinguish this skill."
        )
        for c in weak_clauses[:2]:
            label = f"'{c[:60]}...'" if len(c) > 60 else f"'{c}'"
            reasons.append(f"  -> {label}")
    for m in missing:
        reasons.append(f"Added missing: {m}")
    return "\n".join(reasons)


def _apply_suggestion(file_path: str, new_description: str) -> None:
    """Write improved description back to a skill file's frontmatter."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"(description:\s*).*",
        rf"\g<1>{new_description}",
        content,
        count=1,
    )
    path.write_text(updated, encoding="utf-8")
