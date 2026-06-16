"""Skill description linter — checks individual skill descriptions for quality issues.

Each rule checks a different dimension of description quality:
  - min-length: Description too short to be useful for routing.
  - max-length: Description too long, causes context bloat.
  - no-triggers: Missing trigger phrases that help the agent match intents.
  - vague-terms: Generic words that create routing ambiguity.
  - missing-scope: No scope constraints (when to use vs. not use).
  - no-negative: Doesn't tell the agent when NOT to invoke this skill.
"""

from __future__ import annotations

import re
from pathlib import Path

from skill_distill.models import (
    Issue,
    LintResult,
    Rule,
    Severity,
    Skill,
    VAGUE_WORDS,
)
from skill_distill.parser import parse_directory, parse_file


# ── Rule thresholds ───────────────────────────────────────────────────────────

MIN_DESCRIPTION_CHARS = 50
MAX_DESCRIPTION_CHARS = 500
TRIGGER_KEYWORDS = {
    "use when", "use for", "trigger", "invoke", "适合", "用于",
    "适用场景", "触发",
}


# ── Public API ────────────────────────────────────────────────────────────────


def lint_skills(target: Path) -> LintResult:
    """Run all linter rules against one or more skills."""
    if target.is_file():
        skills = [s for s in [parse_file(target)] if s is not None]
    else:
        skills = parse_directory(target)

    issues: list[Issue] = []
    for skill in skills:
        issues.extend(_check_min_length(skill))
        issues.extend(_check_max_length(skill))
        issues.extend(_check_no_triggers(skill))
        issues.extend(_check_vague_terms(skill))
        issues.extend(_check_missing_scope(skill))
        issues.extend(_check_no_negative(skill))

    return LintResult(skills_checked=len(skills), issues=issues)


def lint_single(skill: Skill) -> list[Issue]:
    """Run all linter rules against a single skill object."""
    issues: list[Issue] = []
    issues.extend(_check_min_length(skill))
    issues.extend(_check_max_length(skill))
    issues.extend(_check_no_triggers(skill))
    issues.extend(_check_vague_terms(skill))
    issues.extend(_check_missing_scope(skill))
    issues.extend(_check_no_negative(skill))
    return issues


# ── Individual rules ──────────────────────────────────────────────────────────


def _check_min_length(skill: Skill) -> list[Issue]:
    if skill.description_length >= MIN_DESCRIPTION_CHARS:
        return []
    return [
        Issue(
            rule=Rule.MIN_LENGTH,
            severity=Severity.WARNING,
            message=f"Description is only {skill.description_length} chars "
            f"(minimum recommended: {MIN_DESCRIPTION_CHARS}).",
            skill_name=skill.name,
            suggestion="Add trigger phrases and scope constraints to help the agent route correctly.",
            location="description",
        )
    ]


def _check_max_length(skill: Skill) -> list[Issue]:
    if skill.description_length <= MAX_DESCRIPTION_CHARS:
        return []
    return [
        Issue(
            rule=Rule.MAX_LENGTH,
            severity=Severity.INFO,
            message=f"Description is {skill.description_length} chars "
            f"(recommended max: {MAX_DESCRIPTION_CHARS}).",
            skill_name=skill.name,
            suggestion="Consider trimming non-essential details. The agent only needs "
            "enough to distinguish this skill from others.",
            location="description",
        )
    ]


def _check_no_triggers(skill: Skill) -> list[Issue]:
    """Check for trigger-like phrases that help the agent know when to invoke."""
    desc_lower = skill.description.lower()
    has_triggers = any(t in desc_lower for t in TRIGGER_KEYWORDS)

    # Also check for imperative verbs as implicit triggers
    imperative_pattern = re.compile(
        r"\b(use|invoke|call|run|apply|activate|trigger|适合|用于)\b",
        re.IGNORECASE,
    )

    if has_triggers or imperative_pattern.search(skill.description):
        return []

    return [
        Issue(
            rule=Rule.NO_TRIGGERS,
            severity=Severity.ERROR,
            message="No trigger phrases found in description.",
            skill_name=skill.name,
            suggestion="Add phrases like 'Use when...', 'Use for...', or 'Trigger: ...' "
            "to help the agent recognize when to invoke this skill.",
            location="description",
        )
    ]


def _check_vague_terms(skill: Skill) -> list[Issue]:
    """Detect generic words that create routing ambiguity."""
    desc_lower = skill.description.lower()
    words = set(re.findall(r"\b\w+\b", desc_lower))
    found = words & VAGUE_WORDS

    if not found:
        return []

    return [
        Issue(
            rule=Rule.VAGUE_TERMS,
            severity=Severity.WARNING,
            message=f"Vague terms found: {', '.join(sorted(found))}.",
            skill_name=skill.name,
            suggestion="Replace generic words with specific, domain-relevant terms. "
            "E.g. 'utility' -> 'CSS grid generator', 'helper' -> 'API response validator'.",
            location="description",
        )
    ]


def _check_missing_scope(skill: Skill) -> list[Issue]:
    """Check if the description defines a clear scope of applicability."""
    scope_patterns = [
        r"\b(when|if|for|适用于|用于|适合)\b",
        r"\b(projects? with|repos? with|code that|files? with)\b",
        r"\b(specifically|only|exclusively|特别是|仅)\b",
    ]

    desc_lower = skill.description.lower()
    has_scope = any(re.search(p, desc_lower, re.IGNORECASE) for p in scope_patterns)

    if has_scope:
        return []

    return [
        Issue(
            rule=Rule.MISSING_SCOPE,
            severity=Severity.WARNING,
            message="Description lacks scope constraint — when should this skill be used?",
            skill_name=skill.name,
            suggestion="Add scope: 'Use when dealing with React components' or "
            "'Use for projects using PostgreSQL'.",
            location="description",
        )
    ]


def _check_no_negative(skill: Skill) -> list[Issue]:
    """Check if the description tells the agent when NOT to use this skill."""
    negative_patterns = [
        r"\bnot\b.*\b(use|for|when|suitable|applicable)\b",
        r"\b(avoid|don't|do not|skip|不要|避免)\b",
        r"\b(instead|alternative|rather than)\b",
    ]

    desc_lower = skill.description.lower()
    has_negative = any(re.search(p, desc_lower, re.IGNORECASE) for p in negative_patterns)

    if has_negative:
        return []

    return [
        Issue(
            rule=Rule.NO_NEGATIVE,
            severity=Severity.INFO,
            message="Description doesn't specify when NOT to use this skill.",
            skill_name=skill.name,
            suggestion="Add a negative constraint to prevent misfires. "
            "E.g. 'NOT for simple scripts — use manual tools for one-liners.'",
            location="description",
        )
    ]
