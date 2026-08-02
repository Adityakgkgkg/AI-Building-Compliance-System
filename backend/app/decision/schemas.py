"""
MCRDSE Sprint 3 – Decision Support Schemas
===========================================
Pydantic v2 strict-typed data models defining the canonical schemas for
recommendations, risk assessment, approval readiness, and decision summaries.

Design rules:
- Strict Pydantic v2 models (`model_config = ConfigDict(strict=True, frozen=True)`).
- No `Any` types allowed.
- Every field maps deterministically from the canonical ``EvidenceBundle``.
- Immutable and serialisable to JSON.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.report.schemas import EvidenceBundle


_STRICT = ConfigDict(strict=True, frozen=True)


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Engine Schemas
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationItem(BaseModel):
    """
    Deterministic, evidence-backed recommendation item generated from a rule evaluation.
    """

    model_config = _STRICT

    recommendation_id: str = Field(
        ...,
        description="Unique identifier for this recommendation (e.g. 'REC-BBMP-FSI-001').",
    )
    rule_id: str = Field(
        ...,
        description="Machine-readable rule identifier from the evidence bundle.",
    )
    rule_name: str = Field(
        ...,
        description="Human-readable rule name.",
    )
    clause: str = Field(
        ...,
        description="Regulatory clause reference (e.g. 'BBMP Bye-law 7.3.2').",
    )
    explanation: str = Field(
        ...,
        description="Plain-language explanation of why this recommendation was triggered.",
    )
    recommended_action: str = Field(
        ...,
        description="Exact corrective action required to achieve compliance.",
    )
    priority: str = Field(
        ...,
        description="Priority classification: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'.",
    )
    severity: str = Field(
        ...,
        description="Original rule severity: 'BLOCKING', 'MAJOR', 'MINOR', or 'INFO'.",
    )
    status: str = Field(
        ...,
        description="Original rule status: 'FAILED' or 'WARNING'.",
    )
    expected: str = Field(
        ...,
        description="Permitted/required regulatory threshold.",
    )
    actual: str = Field(
        ...,
        description="Measured building/site attribute value.",
    )


class RecommendationResponse(BaseModel):
    """
    Aggregated list of evidence-based recommendations ordered by priority.
    """

    model_config = _STRICT

    report_id: str = Field(..., description="UUID4 report identifier.")
    generated_at: datetime = Field(..., description="UTC timestamp of generation.")
    total_recommendations: int = Field(..., ge=0, description="Total recommendation count.")
    critical_count: int = Field(..., ge=0, description="Number of CRITICAL priority items.")
    high_count: int = Field(..., ge=0, description="Number of HIGH priority items.")
    medium_count: int = Field(..., ge=0, description="Number of MEDIUM priority items.")
    low_count: int = Field(..., ge=0, description="Number of LOW priority items.")
    recommendations: List[RecommendationItem] = Field(
        default_factory=list,
        description="Ordered list of recommendations.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Approval Readiness Schemas
# ─────────────────────────────────────────────────────────────────────────────

class WeightBreakdown(BaseModel):
    """
    Detailed component weights and sub-scores for approval readiness.
    """

    model_config = _STRICT

    compliance_subscore: float = Field(..., ge=0.0, le=100.0, description="Compliance score component.")
    blocking_subscore: float = Field(..., ge=0.0, le=100.0, description="Blocking violations component.")
    gis_risk_subscore: float = Field(..., ge=0.0, le=100.0, description="GIS risk component.")
    classification_subscore: float = Field(..., ge=0.0, le=100.0, description="Classification confidence component.")

    compliance_weight: float = Field(..., ge=0.0, le=1.0, description="Weight assigned to compliance subscore.")
    blocking_weight: float = Field(..., ge=0.0, le=1.0, description="Weight assigned to blocking violations.")
    gis_risk_weight: float = Field(..., ge=0.0, le=1.0, description="Weight assigned to GIS risk.")
    classification_weight: float = Field(..., ge=0.0, le=1.0, description="Weight assigned to classification.")


class ApprovalReadiness(BaseModel):
    """
    Weighted approval readiness assessment and sanction verdict.
    """

    model_config = _STRICT

    report_id: str = Field(..., description="UUID4 report identifier.")
    readiness_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall weighted approval readiness score in [0.0, 100.0].",
    )
    status_category: str = Field(
        ...,
        description="Sanction status category: 'APPROVED', 'CONDITIONAL_APPROVAL', 'REQUIRES_MANUAL_REVIEW', or 'REJECTED'.",
    )
    sanction_verdict: str = Field(
        ...,
        description="Official executive sanction verdict string for municipal officers.",
    )
    blocking_violations_count: int = Field(..., ge=0, description="Count of blocking violations.")
    failed_rules_count: int = Field(..., ge=0, description="Count of failed rules.")
    warning_rules_count: int = Field(..., ge=0, description="Count of warning rules.")
    weights: WeightBreakdown = Field(..., description="Breakdown of weights and component sub-scores.")
    key_factors: List[str] = Field(
        default_factory=list,
        description="Key factors influencing the readiness evaluation.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Risk Assessment Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DimensionRisk(BaseModel):
    """
    Risk assessment for a single dimension (Environmental, Zoning, Structural, or Compliance).
    """

    model_config = _STRICT

    dimension_name: str = Field(..., description="Dimension title (e.g. 'Environmental Risk').")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk score in [0.0, 100.0] (higher = riskier).")
    risk_level: str = Field(..., description="Risk level category: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'.")
    key_factors: List[str] = Field(default_factory=list, description="Primary drivers of risk in this dimension.")


class RiskAssessment(BaseModel):
    """
    Comprehensive 4-dimensional risk evaluation.
    """

    model_config = _STRICT

    report_id: str = Field(..., description="UUID4 report identifier.")
    overall_risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite risk score in [0.0, 100.0].")
    overall_risk_level: str = Field(..., description="Highest or composite risk level: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'.")
    environmental_risk: DimensionRisk = Field(..., description="Lake buffer and flood risk evaluation.")
    zoning_risk: DimensionRisk = Field(..., description="Heritage, airport, and land-use compatibility evaluation.")
    structural_risk: DimensionRisk = Field(..., description="Height, FSI, and ground coverage structural risk.")
    compliance_risk: DimensionRisk = Field(..., description="Rule failures and score deficit evaluation.")


# ─────────────────────────────────────────────────────────────────────────────
# Executive Decision Summary Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DecisionSummary(BaseModel):
    """
    Executive decision summary for municipal plan sanctioning officers.
    """

    model_config = _STRICT

    report_id: str = Field(..., description="UUID4 report identifier.")
    building_name: str = Field(..., description="Building name.")
    building_type: str = Field(..., description="Classified building type.")
    authority: str = Field(..., description="Planning authority jurisdiction.")
    ward: str = Field(..., description="BBMP Ward name.")
    sanction_recommendation: str = Field(..., description="Executive sanction recommendation (e.g. 'REFUSE SANCTION').")
    executive_summary_text: str = Field(..., description="Comprehensive multi-paragraph synthesis text.")
    top_risk_factors: List[str] = Field(default_factory=list, description="Top 3–5 risk factors.")
    mandatory_preconditions: List[str] = Field(default_factory=list, description="Mandatory conditions before approval can be considered.")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next action steps for the officer.")


# ─────────────────────────────────────────────────────────────────────────────
# Full Decision Context (Root Object)
# ─────────────────────────────────────────────────────────────────────────────

class DecisionContext(BaseModel):
    """
    Combined decision context containing the evidence bundle and all decision engine outputs.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    evidence_bundle: EvidenceBundle = Field(..., description="Canonical evidence bundle.")
    approval: ApprovalReadiness = Field(..., description="Approval readiness assessment.")
    risk: RiskAssessment = Field(..., description="Risk assessment across 4 dimensions.")
    recommendations: RecommendationResponse = Field(..., description="Prioritized recommendations.")
    summary: DecisionSummary = Field(..., description="Executive decision summary.")
