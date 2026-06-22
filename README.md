# skill-distill

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-7%2F7%20passed-brightgreen)](tests/)
[![Status](https://img.shields.io/badge/status-active-success)](https://github.com/lov-alt/skill-distill)

> Sharpen AI agent skills. Better descriptions = better routing.

**skill-distill** helps you write clear, distinguishable skill descriptions so AI agents (Claude Code, Cursor, etc.) pick the right skill every time — even when you have 50+ skills installed.

## Why?

When your skill library grows, routing accuracy collapses:

| Problem | Data |
| ------- | ---- |
| Skills with descriptions too short to be useful | **44%** of public skills |
| Non-actionable noise in skill body text | **60%+** |
| Routing accuracy without description optimization | **~49%** |
| Routing accuracy with clean, distinct descriptions | **~74%** |

The root cause: **overlapping descriptions create routing ambiguity**. When `api-reviewer`, `code-quality-checker`, and `pr-review-standards` all match "review this PR", the agent has to guess.

skill-distill diagnoses these problems and tells you exactly how to fix them.

## Install

```powershell
# From PyPI (recommended)
pip install skill-distill

# Or bleeding-edge from GitHub
pip install git+https://github.com/lov-alt/skill-distill.git

# With embedding support (better semantic analysis)
pip install skill-distill[embed]
```

## Claude Code Integration

To use skill-distill inside Claude Code conversations — just ask the agent to check your skills and it'll do it automatically:

```powershell
# Install the skill into Claude Code
cp SKILL.md ~/.claude/skills/skill-distill.md
```

Or from the repo:

```powershell
# In your project's .claude/skills/ directory
curl -o .claude/skills/skill-distill.md \
  https://raw.githubusercontent.com/lov-alt/skill-distill/master/SKILL.md
```

Then in conversation: *"Check my skills directory for routing issues"* → Agent picks up skill-distill automatically.

> We [dogfood our own tool](SKILL.md) — the SKILL.md description passes `skill-distill lint` with 0 errors.

---

## Usage

### Lint — check description quality

```bash
# A single skill
skill-distill lint ./skills/my-skill.md

# All skills in a directory
skill-distill lint ./skills/
```

Checks each description for: length, trigger phrases, vague terms, scope constraints, and negative constraints (when NOT to use).

### Diff — find overlapping skills

```bash
skill-distill diff ./skills/ --threshold 0.75
```

Compares all skills pairwise using Jaccard keyword overlap and (optionally) embedding cosine similarity. Flags pairs that an agent would struggle to tell apart.

### Optimize — get improvement suggestions

```bash
# See what would change
skill-distill optimize ./skills/my-skill.md --dry-run

# Apply suggestions
skill-distill optimize ./skills/my-skill.md --apply
```

Decomposes descriptions into semantic clauses, scores each for distinguishability, and suggests removing generic noise while adding trigger phrases and scope constraints.

### Benchmark — measure routing accuracy

```bash
skill-distill bench ./suite.yaml --skills ./skills/ --output report.json
```

Run a test suite of queries against your skills and measure Hit@1, Hit@5, precision, and recall.

Benchmark YAML format:

```yaml
skills_dir: ./skills
test_cases:
  - query: "review this PR for security issues"
    expected: security-code-review
  - query: "create a login form"
    expected: building-forms
```

### Init — create project config

```bash
skill-distill init
```

Creates a `.skill-distill.yaml` config file with customizable rule thresholds.

## How It Works

```
skill-distill lint
  |-- min-length:     description >= 50 chars?
  |-- max-length:     description <= 500 chars?
  |-- no-triggers:    has trigger phrases ("Use when...", "For...")?
  |-- vague-terms:    avoids generic words ("utility", "helper")?
  |-- missing-scope:  defines when to use AND when not to?
  |-- no-negative:    tells the agent when NOT to invoke?

skill-distill diff
  |-- Jaccard similarity on meaningful keywords
  |-- Cosine similarity on sentence embeddings (optional)
  |-- Flags pairs above configurable threshold

skill-distill optimize
  |-- Decomposes description into semantic clauses
  |-- Scores each clause for routing contribution
  |-- Removes generic noise, adds missing constraints
```

## Philosophy

- **Description-first**: The description is the only thing the agent sees before deciding to invoke a skill. Make it count.
- **Less is more**: Removing non-essential content improves routing accuracy (SkillReducer paper: 48% compression, 2.8% quality gain).
- **Mutual exclusivity**: Every skill should have a clear, non-overlapping reason to exist.

## License

MIT
