"""
MCRDSE Sprint 3 – Recommendation Engine
========================================
Generates evidence-backed, deterministic recommendations from an ``EvidenceBundle``.

Rules:
- Zero recalculation of compliance or spatial checks.
- Formulates specific, actionable recommendations for every rule evaluated as ``FAILED`` or ``WARNING``.
- Priority mapping:
    - ``BLOCKING`` severity  → ``CRITICAL`` priority
    - ``MAJOR`` severity     → ``HIGH`` priority
    - ``MINOR`` severity     → ``MEDIUM`` priority
    - ``INFO`` severity      → ``LOW`` priority
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.decision.prioritizer import ViolationPrioritizer
from app.decision.schemas import RecommendationItem, RecommendationResponse
from app.report.schemas import EvidenceBundle, RuleResult


def _map_severity_to_priority(severity: str) -> str:
    """Map rule severity string to recommendation priority category."""
    mapping = {
        "BLOCKING": "CRITICAL",
        "MAJOR": "HIGH",
        "MINOR": "MEDIUM",
        "INFO": "LOW",
    }
    return mapping.get(severity.upper(), "MEDIUM")


class RecommendationEngine:
    """
    Evidence-based recommendation engine.
    """

    @staticmethod
    def generate_recommendations(bundle: EvidenceBundle) -> RecommendationResponse:
        """
        Extract non-passing rules from the evidence bundle and construct prioritized recommendations.

        Parameters
        ----------
        bundle:
            Canonical EvidenceBundle.

        Returns
        -------
        RecommendationResponse
            Aggregated, prioritized recommendations payload.
        """
        raw_items: List[RecommendationItem] = []

        for rule in bundle.compliance.rule_results:
            # We construct recommendations for non-passed rules (FAILED or WARNING)
            if rule.status in ("FAILED", "WARNING"):
                priority = _map_severity_to_priority(rule.severity)

                # Formulate evidence-based explanation & action if recommendation field is empty or generic
                explanation = rule.message
                if rule.difference and rule.difference != "0":
                    explanation += f" (Deviation: {rule.difference})."

                action = rule.recommendation
                if not action or action == "No corrective action required.":
                    if rule.status == "FAILED":
                        action = f"Modify building design to satisfy {rule.clause}. Expected {rule.expected}, found {rule.actual}."
                    else:
                        action = f"Review design against {rule.clause} requirements."

                rec_item = RecommendationItem(
                    recommendation_id=f"REC-{rule.rule_id}",
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    clause=rule.clause,
                    explanation=explanation,
                    recommended_action=action,
                    priority=priority,
                    severity=rule.severity,
                    status=rule.status,
                    expected=rule.expected,
                    actual=rule.actual,
                )
                raw_items.append(rec_item)

        # Sort recommendations using deterministic prioritizer
        sorted_recs = ViolationPrioritizer.sort_recommendations(raw_items)

        # Compute priority counts
        critical = sum(1 for r in sorted_recs if r.priority == "CRITICAL")
        high = sum(1 for r in sorted_recs if r.priority == "HIGH")
        medium = sum(1 for r in sorted_recs if r.priority == "MEDIUM")
        low = sum(1 for r in sorted_recs if r.priority == "LOW")

        return RecommendationResponse(
            report_id=bundle.report_id,
            generated_at=datetime.now(timezone.utc),
            total_recommendations=len(sorted_recs),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            recommendations=sorted_recs,
        )
