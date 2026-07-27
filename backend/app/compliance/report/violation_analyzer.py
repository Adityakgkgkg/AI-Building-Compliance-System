"""
AI Building Compliance System — Violation Analyzer

Enriches and groups rule evaluation results for the report.

Responsibilities:
  - Separate results into violations / warnings / passed / not_applicable / skipped
  - Group results by category
  - Sort violations by priority (lowest number = highest priority)
  - Compute per-category compliance status
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from app.compliance.schemas import CategoryResult, RuleResult, RuleStatus

logger = logging.getLogger(__name__)


def analyze(
    results: List[RuleResult],
) -> Tuple[
    List[RuleResult],   # violations (FAILED)
    List[RuleResult],   # warnings (WARNING)
    List[RuleResult],   # passed
    List[RuleResult],   # failed_rules (FAILED + WARNING combined)
    List[RuleResult],   # not_applicable
    List[RuleResult],   # skipped
    List[CategoryResult],  # category_results
]:
    """
    Analyze and categorize rule results.

    Returns:
        Tuple of (violations, warnings, passed, failed_rules, not_applicable, skipped, categories).
    """
    violations: List[RuleResult] = []
    warnings:   List[RuleResult] = []
    passed:     List[RuleResult] = []
    failed:     List[RuleResult] = []
    not_applicable: List[RuleResult] = []
    skipped:    List[RuleResult] = []

    for r in results:
        if r.status == RuleStatus.FAILED:
            violations.append(r)
            failed.append(r)
        elif r.status == RuleStatus.WARNING:
            warnings.append(r)
            failed.append(r)
        elif r.status == RuleStatus.PASSED:
            passed.append(r)
        elif r.status == RuleStatus.NOT_APPLICABLE:
            not_applicable.append(r)
        elif r.status == RuleStatus.SKIPPED:
            skipped.append(r)

    # Sort violations by priority (lower number = higher priority)
    violations.sort(key=lambda r: r.priority)
    warnings.sort(key=lambda r: r.priority)

    categories = _group_by_category(results)

    logger.debug(
        "Analysis: %d violations, %d warnings, %d passed, %d na, %d skipped",
        len(violations), len(warnings), len(passed),
        len(not_applicable), len(skipped),
    )

    return violations, warnings, passed, failed, not_applicable, skipped, categories


def _group_by_category(results: List[RuleResult]) -> List[CategoryResult]:
    """Group results by category and compute per-category status."""
    buckets: Dict[str, List[RuleResult]] = defaultdict(list)
    for r in results:
        buckets[r.category].append(r)

    category_results: List[CategoryResult] = []
    for category, cat_rules in buckets.items():
        n_passed = sum(1 for r in cat_rules if r.status == RuleStatus.PASSED)
        n_failed = sum(1 for r in cat_rules if r.status == RuleStatus.FAILED)
        n_warn   = sum(1 for r in cat_rules if r.status == RuleStatus.WARNING)
        n_na     = sum(1 for r in cat_rules if r.status == RuleStatus.NOT_APPLICABLE)
        n_skip   = sum(1 for r in cat_rules if r.status == RuleStatus.SKIPPED)

        if n_failed > 0:
            cat_status = "NON_COMPLIANT"
        elif n_warn > 0:
            cat_status = "CONDITIONALLY_COMPLIANT"
        elif n_passed > 0:
            cat_status = "COMPLIANT"
        else:
            cat_status = "INSUFFICIENT_DATA"

        category_results.append(
            CategoryResult(
                category=category,
                status=cat_status,
                total_rules=len(cat_rules),
                passed=n_passed,
                failed=n_failed,
                warnings=n_warn,
                not_applicable=n_na,
                skipped=n_skip,
                rules=cat_rules,
            )
        )

    return category_results
