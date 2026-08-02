"""
MCRDSE Sprint 3 – Approval Readiness Engine
===========================================
Evaluates an ``EvidenceBundle`` using a configurable weighted scoring model to compute
an overall approval readiness score [0.0, 100.0] and assign a sanction status category:

Status categories:
- ``APPROVED``: score >= 90.0, 0 blocking violations, 0 failed rules.
- ``CONDITIONAL_APPROVAL``: score >= 70.0, 0 blocking violations.
- ``REQUIRES_MANUAL_REVIEW``: score >= 50.0 or warnings > 0.
- ``REJECTED``: score < 50.0 or blocking > 0.
"""

from __future__ import annotations

from typing import List, Optional
from app.decision.schemas import ApprovalReadiness, WeightBreakdown
from app.report.schemas import EvidenceBundle


class ApprovalReadinessEngine:
    """
    Weighted scoring engine for municipal plan approval readiness.
    """

    def __init__(
        self,
        compliance_weight: float = 0.40,
        blocking_weight: float = 0.30,
        gis_risk_weight: float = 0.20,
        classification_weight: float = 0.10,
    ) -> None:
        """
        Initialize the engine with configurable weights (must sum to 1.0).
        """
        total = compliance_weight + blocking_weight + gis_risk_weight + classification_weight
        if abs(total - 1.0) > 1e-4:
            # Normalize if weights don't sum strictly to 1.0
            compliance_weight /= total
            blocking_weight /= total
            gis_risk_weight /= total
            classification_weight /= total

        self.compliance_weight = compliance_weight
        self.blocking_weight = blocking_weight
        self.gis_risk_weight = gis_risk_weight
        self.classification_weight = classification_weight

    def evaluate_readiness(self, bundle: EvidenceBundle) -> ApprovalReadiness:
        """
        Compute readiness score, status category, and key factors from EvidenceBundle.
        """
        comp = bundle.compliance
        gis = bundle.gis
        cls = bundle.classification

        # 1. Compliance subscore [0..100]
        compliance_sub = max(0.0, min(100.0, comp.score))

        # 2. Blocking violations subscore [0..100]
        # 0 blocking = 100.0; 1 blocking = 50.0; >= 2 blocking = 0.0
        if comp.blocking == 0:
            blocking_sub = 100.0
        elif comp.blocking == 1:
            blocking_sub = 50.0
        else:
            blocking_sub = 0.0

        # 3. GIS risk subscore [0..100] (100 = low risk, 0 = high risk)
        gis_penalty = 0.0
        if gis.lake_buffer:
            gis_penalty += 40.0
        if gis.airport_zone:
            gis_penalty += 20.0
        if gis.flood_risk.upper() == "HIGH":
            gis_penalty += 30.0
        elif gis.flood_risk.upper() == "MEDIUM":
            gis_penalty += 15.0
        if gis.heritage_zone:
            gis_penalty += 10.0

        gis_sub = max(0.0, 100.0 - gis_penalty)

        # 4. Classification subscore [0..100]
        classification_sub = max(0.0, min(100.0, cls.confidence * 100.0))

        # Weighted total score
        total_score = (
            compliance_sub * self.compliance_weight
            + blocking_sub * self.blocking_weight
            + gis_sub * self.gis_risk_weight
            + classification_sub * self.classification_weight
        )
        total_score = round(max(0.0, min(100.0, total_score)), 2)

        # Key factors & Category determination
        key_factors: List[str] = []

        if comp.blocking > 0:
            key_factors.append(f"Contains {comp.blocking} BLOCKING violation(s) preventing automatic sanction.")
        if comp.failed > 0:
            key_factors.append(f"{comp.failed} compliance rule(s) failed evaluation.")
        if comp.warnings > 0:
            key_factors.append(f"{comp.warnings} compliance rule warning(s) logged.")
        if gis.lake_buffer:
            key_factors.append("Site falls within a regulated lake buffer zone.")
        if gis.airport_zone:
            key_factors.append("Site falls within airport height restriction funnel.")
        if gis.flood_risk.upper() in ("MEDIUM", "HIGH"):
            key_factors.append(f"Site is designated as {gis.flood_risk} flood risk zone.")

        if not key_factors:
            key_factors.append("All statutory compliance rules passed with zero spatial constraints.")

        # Determine status category
        if comp.blocking > 0 or total_score < 50.0:
            status_category = "REJECTED"
            sanction_verdict = (
                "SANCTION REFUSED — Building plan violates critical statutory bye-laws "
                f"({comp.blocking} blocking violation(s), score: {total_score}/100)."
            )
        elif total_score >= 90.0 and comp.failed == 0:
            status_category = "APPROVED"
            sanction_verdict = (
                "PLAN SANCTION APPROVED — Building plan complies with all statutory regulations "
                f"and municipal bye-laws (score: {total_score}/100)."
            )
        elif total_score >= 70.0:
            status_category = "CONDITIONAL_APPROVAL"
            sanction_verdict = (
                "CONDITIONAL SANCTION RECOMMENDED — Plan meets primary statutory standards but requires "
                f"fulfillment of minor compliance conditions prior to permit issuance (score: {total_score}/100)."
            )
        else:
            status_category = "REQUIRES_MANUAL_REVIEW"
            sanction_verdict = (
                "MANUAL COMMITTEE REVIEW REQUIRED — Plan exhibits regulatory warnings or marginal parameters "
                f"requiring officer inspection (score: {total_score}/100)."
            )

        weights_breakdown = WeightBreakdown(
            compliance_subscore=round(compliance_sub, 2),
            blocking_subscore=round(blocking_sub, 2),
            gis_risk_subscore=round(gis_sub, 2),
            classification_subscore=round(classification_sub, 2),
            compliance_weight=self.compliance_weight,
            blocking_weight=self.blocking_weight,
            gis_risk_weight=self.gis_risk_weight,
            classification_weight=self.classification_weight,
        )

        return ApprovalReadiness(
            report_id=bundle.report_id,
            readiness_score=total_score,
            status_category=status_category,
            sanction_verdict=sanction_verdict,
            blocking_violations_count=comp.blocking,
            failed_rules_count=comp.failed,
            warning_rules_count=comp.warnings,
            weights=weights_breakdown,
            key_factors=key_factors,
        )
