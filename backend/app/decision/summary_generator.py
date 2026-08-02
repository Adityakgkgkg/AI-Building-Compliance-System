"""
MCRDSE Sprint 3 – Decision Summary Generator
=============================================
Synthesizes evidence, approval readiness, risk assessment, and recommendations into an
executive decision summary for municipal plan sanctioning officers.
"""

from __future__ import annotations

from typing import List
from app.decision.schemas import (
    ApprovalReadiness,
    DecisionSummary,
    RecommendationResponse,
    RiskAssessment,
)
from app.report.schemas import EvidenceBundle


class DecisionSummaryGenerator:
    """
    Synthesizer for executive municipal decision summaries.
    """

    @staticmethod
    def generate_summary(
        bundle: EvidenceBundle,
        approval: ApprovalReadiness,
        risk: RiskAssessment,
        recommendations: RecommendationResponse,
    ) -> DecisionSummary:
        """
        Generate executive decision summary object.
        """
        bld = bundle.building
        cls = bundle.classification
        gis = bundle.gis

        # Determine sanction recommendation string
        if approval.status_category == "APPROVED":
            sanction_rec = "GRANT BUILDING PERMIT SANCTION"
        elif approval.status_category == "CONDITIONAL_APPROVAL":
            sanction_rec = "GRANT CONDITIONAL SANCTION (Pending Compliance Fulfillment)"
        elif approval.status_category == "REQUIRES_MANUAL_REVIEW":
            sanction_rec = "REFER TO MUNICIPAL PLANNING COMMITTEE FOR MANUAL REVIEW"
        else:
            sanction_rec = "REFUSE PLAN SANCTION — MANDATORY REJECTION"

        # Executive summary multi-paragraph text
        summary_lines = [
            f"EXECUTIVE SANCTION SUMMARY | Report ID: {bundle.report_id}",
            f"Building: '{bld.building_name}' ({bld.building_id}) | Type: {cls.predicted_type} | Ward: {gis.ward} ({gis.zone}).",
            f"Official Verdict: {approval.sanction_verdict}",
            f"Readiness Score: {approval.readiness_score:.1f}/100 | Overall Risk Level: {risk.overall_risk_level} (Score: {risk.overall_risk_score:.1f}/100).",
            f"Evaluated Rules: {bundle.compliance.rules_checked} total ({bundle.compliance.passed} Passed, {bundle.compliance.failed} Failed, {bundle.compliance.warnings} Warnings, {bundle.compliance.blocking} Blocking).",
        ]

        if approval.status_category == "REJECTED":
            summary_lines.append(
                "CRITICAL NOTICE: Sanction must be refused in accordance with municipal statutory bye-laws due to blocking compliance violations or severe risk factors."
            )
        elif approval.status_category == "CONDITIONAL_APPROVAL":
            summary_lines.append(
                "NOTICE: Plan meets structural safety criteria. Conditional permit may be issued upon submission of rectified drawings addressing minor non-blocking violations."
            )

        executive_text = "\n".join(summary_lines)

        # Extract top risk factors across dimensions
        top_risks: List[str] = []
        for dim in (risk.compliance_risk, risk.environmental_risk, risk.zoning_risk, risk.structural_risk):
            for factor in dim.key_factors:
                if "zero" not in factor.lower() and "no adverse" not in factor.lower() and "fully compatible" not in factor.lower() and "within standard" not in factor.lower():
                    top_risks.append(f"[{dim.dimension_name}] {factor}")

        if not top_risks:
            top_risks.append("No critical risk factors identified.")

        # Mandatory preconditions
        preconditions: List[str] = []
        for rec in recommendations.recommendations:
            if rec.priority in ("CRITICAL", "HIGH"):
                preconditions.append(f"Rectify {rec.rule_id} ({rec.clause}): {rec.recommended_action}")

        if not preconditions and approval.status_category != "APPROVED":
            preconditions.append("Submit updated architectural plans addressing reported warnings.")

        # Next steps
        next_steps: List[str] = []
        if approval.status_category == "APPROVED":
            next_steps.append("Issue digital Sanction Certificate and approved plan blueprint.")
            next_steps.append("Archive evidence bundle in municipal GIS registry.")
        elif approval.status_category == "CONDITIONAL_APPROVAL":
            next_steps.append("Issue Conditional Sanction Notice to applicant.")
            next_steps.append("Require resubmission of rectified IFC model within 30 days.")
        elif approval.status_category == "REQUIRES_MANUAL_REVIEW":
            next_steps.append("Schedule file for Urban Development Committee review agenda.")
            next_steps.append("Conduct site inspection if spatial discrepancies persist.")
        else: # REJECTED
            next_steps.append("Issue formal Rejection Order detailing statutory bye-law violations.")
            next_steps.append("Notify applicant of appeal procedures under Municipal Act.")

        return DecisionSummary(
            report_id=bundle.report_id,
            building_name=bld.building_name,
            building_type=cls.predicted_type,
            authority=gis.authority,
            ward=gis.ward,
            sanction_recommendation=sanction_rec,
            executive_summary_text=executive_text,
            top_risk_factors=top_risks[:5],  # Top 5
            mandatory_preconditions=preconditions[:5],
            next_steps=next_steps,
        )
