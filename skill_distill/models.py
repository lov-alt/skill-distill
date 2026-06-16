"""Core data models for the skill-distill toolkit.

Skill, Issue, DiffResult — the three pillars of skill quality analysis.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


# ── Enums ────────────────────────────────────────────────────────────────────


class Severity(str, Enum):
    """Issue severity following the standard error/warning/info convention."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Rule(str, Enum):
    """All linter rules. Each maps to a specific quality dimension."""

    MIN_LENGTH = "min-length"
    MAX_LENGTH = "max-length"
    NO_TRIGGERS = "no-triggers"
    VAGUE_TERMS = "vague-terms"
    MISSING_SCOPE = "missing-scope"
    NO_NEGATIVE = "no-negative"


# ── Word lists ────────────────────────────────────────────────────────────────

VAGUE_WORDS: frozenset[str] = frozenset({
    "helper", "utility", "misc", "miscellaneous", "tool",
    "thing", "various", "etc", "general", "generic",
    "common", "shared", "basic", "simple", "just",
})


# ── Core Models ───────────────────────────────────────────────────────────────


class Skill(BaseModel):
    """A parsed skill with its routing-critical metadata.

    Attributes:
        name: The skill identifier (e.g. 'code-review', 'gsap-hero-animations').
        description: The one-line routing description shown in the agent's system prompt.
        body: The full skill markdown body (loaded on-demand by the agent).
        path: Filesystem path to the skill file, if parsed from disk.
        source: Origin framework — 'claude-code', 'cursor', 'generic', etc.
    """

    name: str
    description: str
    body: str = ""
    path: Path | None = None
    source: str = "unknown"

    @field_validator("description")
    @classmethod
    def _description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Skill description must not be empty.")
        return v.strip()

    @property
    def description_length(self) -> int:
        return len(self.description)

    @property
    def token_estimate(self) -> int:
        """Rough token count (chars / 4). Conservative for English text."""
        return max(1, len(self.description) // 4)


class Issue(BaseModel):
    """A single quality issue found in a skill description."""

    rule: Rule
    severity: Severity
    message: str
    skill_name: str = ""
    suggestion: str = ""
    location: str = ""

    def rich_icon(self) -> str:
        return {"error": "ERR", "warning": "WARN", "info": "INFO"}.get(self.severity, "  ")


class DiffPair(BaseModel):
    """A pair of skills with overlapping descriptions."""

    skill_a: str
    skill_b: str
    cosine_similarity: float
    jaccard_overlap: float
    shared_terms: list[str] = Field(default_factory=list)
    suggestion: str = ""


class DiffResult(BaseModel):
    """Complete diff analysis over a skill set."""

    skills_compared: int
    pairs_flagged: int
    pairs: list[DiffPair] = Field(default_factory=list)
    threshold: float = 0.75


class BenchmarkCase(BaseModel):
    """A single routing test case."""

    query: str
    expected: str
    acceptable: list[str] = Field(default_factory=list)


class BenchmarkSuite(BaseModel):
    """A complete benchmark suite loaded from YAML."""

    skills_dir: Path
    test_cases: list[BenchmarkCase]


class BenchmarkResult(BaseModel):
    """Results from running a benchmark suite."""

    hit_at_1: float
    hit_at_5: float
    precision: float
    recall: float
    confusion: dict[str, dict[str, int]] = Field(default_factory=dict)
    total_cases: int = 0
    passed: int = 0


class LintResult(BaseModel):
    """Aggregated lint results for one or more skills."""

    skills_checked: int
    issues: list[Issue] = Field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def info(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.INFO]

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0
