---
name: skill-distill
description: Audit skill descriptions for routing quality. Use when the user asks to check, lint, audit, or improve AI agent skill descriptions, wants to find overlapping or confusingly similar skills, or needs to benchmark skill routing accuracy. Use for directories containing SKILL.md or similar markdown skill definition files. Not for general code review, not for reviewing pull requests, not for linting regular source code.
---

# Skill Distill

Run the `skill-distill` CLI to analyze AI agent skill descriptions for routing quality issues.

## Prerequisites

- Python 3.10+
- `skill-distill` installed: `pip install skill-distill`

## Commands

### Lint — check description quality

```bash
skill-distill lint <path-to-skills-directory>
```

Checks each skill for: minimum length, trigger phrases, vague terms, scope
constraints, and negative constraints.

### Diff — find overlapping skills

```bash
skill-distill diff <path-to-skills-directory>
```

Compares all skills pairwise to find descriptions that an agent would struggle to
tell apart.

### Optimize — get improvement suggestions

```bash
skill-distill optimize <path-to-skill-file> --dry-run
```

Suggests specific changes to make descriptions more distinguishable.

### Benchmark — measure routing accuracy

```bash
skill-distill bench <benchmark-yaml> --skills <skills-directory>
```

Run a test suite of natural language queries and measure Hit@1, Hit@5, precision,
and recall.

## Example workflow

1. `skill-distill lint ./skills/` — check all skills
2. `skill-distill diff ./skills/` — find overlapping pairs
3. `skill-distill optimize ./skills/problem-skill.md --apply` — fix issues
4. `skill-distill bench suite.yaml --skills ./skills/` — verify improvement
