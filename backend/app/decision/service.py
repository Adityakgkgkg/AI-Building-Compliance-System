"""
MCRDSE Sprint 3 – Decision Support Service Layer
=================================================
``DecisionService`` coordinates all decision support engines:
- Recommendation Engine
- Risk Assessment Engine
- Approval Readiness Engine
- Decision Summary Generator

It uses ``ReportService.collect_evidence`` to obtain the canonical ``EvidenceBundle``
and translates upstream module errors into structured ``ModuleErrorDetail`` tuples.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple, Union

from app.decision.approval_engine import ApprovalReadinessEngine
from app.decision.recommendation_engine import RecommendationEngine
from app.decision.risk_engine import RiskAssessmentEngine
from app.decision.schemas import (
    ApprovalReadiness,
    DecisionContext,
    DecisionSummary,
    RecommendationResponse,
    RiskAssessment,
)
from app.decision.summary_generator import DecisionSummaryGenerator
from app.report.schemas import EvidenceBundle, ModuleErrorDetail
from app.report.service import ReportService


logger = logging.getLogger("app.decision.service")

# Type alias: service returns result or structured error tuple
ServiceResult = Union[DecisionContext, Tuple[ModuleErrorDetail, int]]
ApprovalResult = Union[ApprovalReadiness, Tuple[ModuleErrorDetail, int]]
RiskResult = Union[RiskAssessment, Tuple[ModuleErrorDetail, int]]
RecResult = Union[RecommendationResponse, Tuple[ModuleErrorDetail, int]]
SummaryResult = Union[DecisionSummary, Tuple[ModuleErrorDetail, int]]


class DecisionService:
    """
    Orchestration service for Module 4 Sprint 3 Decision Support.
    """

    @staticmethod
    def get_decision_context(
        ifc_file: str,
        lat: float,
        lon: float,
        bundle: Optional[EvidenceBundle] = None,
    ) -> ServiceResult:
        """
        Fetch evidence bundle (if not provided) and run all decision engines.

        Returns
        -------
        DecisionContext or (ModuleErrorDetail, status_code)
        """
        if bundle is None:
            result = ReportService.collect_evidence(ifc_file=ifc_file, lat=lat, lon=lon)
            if not isinstance(result, EvidenceBundle):
                # Upstream module error tuple
                return result
            bundle = result

        # Run decision engines
        approval_engine = ApprovalReadinessEngine()
        approval = approval_engine.evaluate_readiness(bundle)

        risk = RiskAssessmentEngine.evaluate_risk(bundle)

        recommendations = RecommendationEngine.generate_recommendations(bundle)

        summary = DecisionSummaryGenerator.generate_summary(
            bundle=bundle,
            approval=approval,
            risk=risk,
            recommendations=recommendations,
        )

        return DecisionContext(
            evidence_bundle=bundle,
            approval=approval,
            risk=risk,
            recommendations=recommendations,
            summary=summary,
        )

    @staticmethod
    def get_approval_readiness(
        ifc_file: str,
        lat: float,
        lon: float,
        bundle: Optional[EvidenceBundle] = None,
    ) -> ApprovalResult:
        """Fetch approval readiness assessment."""
        res = DecisionService.get_decision_context(ifc_file=ifc_file, lat=lat, lon=lon, bundle=bundle)
        if isinstance(res, tuple):
            return res
        return res.approval

    @staticmethod
    def get_risk_assessment(
        ifc_file: str,
        lat: float,
        lon: float,
        bundle: Optional[EvidenceBundle] = None,
    ) -> RiskResult:
        """Fetch risk assessment."""
        res = DecisionService.get_decision_context(ifc_file=ifc_file, lat=lat, lon=lon, bundle=bundle)
        if isinstance(res, tuple):
            return res
        return res.risk

    @staticmethod
    def get_recommendations(
        ifc_file: str,
        lat: float,
        lon: float,
        bundle: Optional[EvidenceBundle] = None,
    ) -> RecResult:
        """Fetch recommendations response."""
        res = DecisionService.get_decision_context(ifc_file=ifc_file, lat=lat, lon=lon, bundle=bundle)
        if isinstance(res, tuple):
            return res
        return res.recommendations

    @staticmethod
    def get_decision_summary(
        ifc_file: str,
        lat: float,
        lon: float,
        bundle: Optional[EvidenceBundle] = None,
    ) -> SummaryResult:
        """Fetch decision summary."""
        res = DecisionService.get_decision_context(ifc_file=ifc_file, lat=lat, lon=lon, bundle=bundle)
        if isinstance(res, tuple):
            return res
        return res.summary
