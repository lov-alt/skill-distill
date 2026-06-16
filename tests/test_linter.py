"""Tests for the linter module."""

from pathlib import Path

from skill_distill.linter import lint_skills
from skill_distill.parser import parse_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_lint_good_skill_has_no_errors():
    result = lint_skills(FIXTURES / "good-skill.md")
    assert result.skills_checked == 1
    assert len(result.errors) == 0


def test_lint_vague_skill_has_errors():
    result = lint_skills(FIXTURES / "vague-skill.md")
    assert result.skills_checked == 1
    assert len(result.errors) >= 1
    assert any(i.rule.value == "no-triggers" for i in result.errors)


def test_parse_good_skill():
    skill = parse_file(FIXTURES / "good-skill.md")
    assert skill is not None
    assert skill.name == "security-code-review"
    assert "security" in skill.description.lower()
    assert len(skill.description) >= 50


def test_parse_vague_skill():
    skill = parse_file(FIXTURES / "vague-skill.md")
    assert skill is not None
    assert skill.name == "helper-tool"
    assert len(skill.description) < 50


def test_lint_all_fixtures_returns_result():
    result = lint_skills(FIXTURES)
    assert result.skills_checked == 4
    assert len(result.issues) > 0
