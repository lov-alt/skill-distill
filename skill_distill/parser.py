"""Skill file parser — reads skill definitions from multiple formats.

Supports:
  - Claude Code SKILL.md (YAML frontmatter + markdown body)
  - Generic markdown with frontmatter
  - Plain text (name derived from filename, content as description)
"""

from __future__ import annotations

import re
from pathlib import Path

from skill_distill.models import Skill

# Claude Code's SKILL.md frontmatter format:
#   ---
#   name: code-review
#   description: Review code for bugs, style, and security issues.
#   ---

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)
_YAML_KV_RE = re.compile(r"^(\w[\w-]*):\s*(.*?)$")


def parse_file(path: str | Path) -> Skill | None:
    """Parse a single skill file. Returns None if unparseable."""
    path = Path(path)
    if not path.is_file():
        return None

    text = path.read_text(encoding="utf-8", errors="replace")
    return _extract_skill(text, path)


def parse_directory(directory: str | Path, pattern: str = "*.md") -> list[Skill]:
    """Parse all skill files in a directory tree."""
    skills: list[Skill] = []
    for md_file in Path(directory).rglob(pattern):
        skill = parse_file(md_file)
        if skill is not None:
            skills.append(skill)
    return skills


def _extract_skill(text: str, path: Path) -> Skill | None:
    """Extract skill metadata from text content.

    Strategy:
      1. Try YAML frontmatter (Claude Code format).
      2. Fall back to first heading + first paragraph.
      3. Last resort: filename as name, first line as description.
    """
    name = ""
    description = ""
    body = ""
    source = "generic"

    fm_match = _FRONTMATTER_RE.match(text.strip())
    if fm_match:
        frontmatter = fm_match.group(1)
        body = fm_match.group(2).strip()
        source = "claude-code"

        fm_data: dict[str, str] = {}
        for line in frontmatter.split("\n"):
            line = line.strip()
            kv = _YAML_KV_RE.match(line)
            if kv:
                fm_data[kv.group(1).strip()] = kv.group(2).strip()

        name = fm_data.get("name", "")
        description = fm_data.get("description", "")

    # Fallback: first heading as name, first non-empty line after as description
    if not name:
        heading_match = re.match(r"^#\s+(.+)", text.strip())
        if heading_match:
            name = heading_match.group(1).strip().lower().replace(" ", "-")
            # Grab the first paragraph after the heading
            rest = text[heading_match.end():].strip()
            para_end = rest.find("\n\n")
            if para_end == -1:
                para_end = len(rest)
            description = rest[:para_end].strip()

    # Last resort: filename
    if not name:
        name = path.stem

    if not description:
        description = name

    return Skill(
        name=name,
        description=description,
        body=body or text,
        path=path,
        source=source,
    )
