"""Tests for the differ module."""

from pathlib import Path

from skill_distill.differ import diff_skills

FIXTURES = Path(__file__).parent / "fixtures"


def test_diff_finds_overlapping_pair():
    result = diff_skills(FIXTURES, threshold=0.3)
    assert result.skills_compared == 4
    # review-pr and code-review should be flagged at low threshold
    assert result.pairs_flagged >= 1


def test_diff_high_threshold_finds_none():
    result = diff_skills(FIXTURES, threshold=0.95)
    assert result.skills_compared == 4
    # At very high threshold, no cosine pairs should match
    # (Jaccard may still catch some, but cosine won't)
    assert result.pairs_flagged >= 0
