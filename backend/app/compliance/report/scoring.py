"""
AI Building Compliance System — Compliance Scoring

Computes the compliance score (0–100) from a list of RuleResult objects.

Scoring formula:
  evaluable = PASSED + FAILED + WARNING  (excludes NOT_APPLICABLE, SKIPPED, placeholders)
  weighted  = PASSED + (WARNING × 0.5)
  score     = (weighted / evaluable) × 100    [rounds to nearest int]

Edge cases:
  evaluable == 0  → 100 (no evaluable rules means full compliance by default)
  all skipped/NA  → 100
"""

from __future__ import annotations

from typing import List

from app.compliance.schemas import RuleResult, RuleStatus


def compute_score(results: List[RuleResult]) -> int:
    """
    Compute the compliance score from 0 to 100.

    Args:
        results: Full list of RuleResult objects.

    Returns:
        Integer compliance score (0–100).
    """
    evaluable = [
        r for r in results
        if r.status in (RuleStatus.PASSED, RuleStatus.FAILED, RuleStatus.WARNING)
        and not r.is_placeholder
    ]

    if not evaluable:
        return 100

    passed   = sum(1.0 for r in evaluable if r.status == RuleStatus.PASSED)
    warnings = sum(0.5 for r in evaluable if r.status == RuleStatus.WARNING)

    score = ((passed + warnings) / len(evaluable)) * 100
    return max(0, min(100, round(score)))
