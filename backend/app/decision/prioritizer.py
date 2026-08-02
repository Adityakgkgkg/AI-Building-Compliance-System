"""
MCRDSE Sprint 3 – Violation Prioritizer
=========================================
Sorts and ranks compliance rule findings and recommendation items deterministically
based on severity, evaluation status, and rule identifiers.
"""

from __future__ import annotations

from typing import List
from app.decision.schemas import RecommendationItem
from app.report.schemas import RuleResult


_SEVERITY_ORDER: dict[str, int] = {
    "BLOCKING": 0,
    "MAJOR": 1,
    "MINOR": 2,
    "INFO": 3,
}

_PRIORITY_ORDER: dict[str, int] = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}

_STATUS_ORDER: dict[str, int] = {
    "FAILED": 0,
    "WARNING": 1,
    "PASSED": 2,
}


class ViolationPrioritizer:
    """
    Deterministic prioritizer for rule evaluation results and recommendations.
    """

    @staticmethod
    def sort_rule_results(rules: List[RuleResult]) -> List[RuleResult]:
        """
        Sort RuleResult items by Severity (BLOCKING first), Status (FAILED first), then Rule ID.
        """
        return sorted(
            rules,
            key=lambda r: (
                _SEVERITY_ORDER.get(r.severity, 99),
                _STATUS_ORDER.get(r.status, 99),
                r.rule_id,
            ),
        )

    @staticmethod
    def sort_recommendations(recommendations: List[RecommendationItem]) -> List[RecommendationItem]:
        """
        Sort RecommendationItem records by Priority (CRITICAL first), Severity, Status, then Rule ID.
        """
        return sorted(
            recommendations,
            key=lambda rec: (
                _PRIORITY_ORDER.get(rec.priority, 99),
                _SEVERITY_ORDER.get(rec.severity, 99),
                _STATUS_ORDER.get(rec.status, 99),
                rec.rule_id,
            ),
        )
