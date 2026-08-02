"""
MCRDSE Sprint 3 – Risk Assessment Engine
========================================
Evaluates an ``EvidenceBundle`` across 4 risk dimensions:
1. Environmental Risk (lake buffers, flood risk)
2. Zoning Risk (heritage conservation, airport funnel, land use)
3. Structural Risk (building height, FSI overload, ground coverage)
4. Compliance Risk (failed rules, blocking violations, score deficit)

Computes per-dimension scores/levels and composite overall risk.
"""

from __future__ import annotations

from typing import List, Tuple
from app.decision.schemas import DimensionRisk, RiskAssessment
from app.report.schemas import EvidenceBundle


def _score_to_level(score: float) -> str:
    """Map numeric risk score [0..100] to risk level category."""
    if score >= 70.0:
        return "CRITICAL"
    if score >= 40.0:
        return "HIGH"
    if score >= 20.0:
        return "MEDIUM"
    return "LOW"


_LEVEL_RANK: dict[str, int] = {
    "CRITICAL": 3,
    "HIGH": 2,
    "MEDIUM": 1,
    "LOW": 0,
}


class RiskAssessmentEngine:
    """
    Multi-dimensional risk assessment engine.
    """

    @staticmethod
    def evaluate_risk(bundle: EvidenceBundle) -> RiskAssessment:
        """
        Perform 4-dimensional risk evaluation on the canonical EvidenceBundle.
        """
        bld = bundle.building
        gis = bundle.gis
        cmp = bundle.compliance

        # ── 1. Environmental Risk ─────────────────────────────────────────────
        env_score = 0.0
        env_factors: List[str] = []

        if gis.lake_buffer:
            env_score += 50.0
            env_factors.append("Site falls inside regulated lake buffer zone.")

        if gis.flood_risk.upper() == "HIGH":
            env_score += 40.0
            env_factors.append("Designated high flood risk area.")
        elif gis.flood_risk.upper() == "MEDIUM":
            env_score += 20.0
            env_factors.append("Designated medium flood risk area.")

        if not env_factors:
            env_factors.append("No adverse environmental or hydrological constraints detected.")

        env_score = round(min(100.0, env_score), 2)
        env_risk = DimensionRisk(
            dimension_name="Environmental Risk",
            risk_score=env_score,
            risk_level=_score_to_level(env_score),
            key_factors=env_factors,
        )

        # ── 2. Zoning Risk ────────────────────────────────────────────────────
        zoning_score = 0.0
        zoning_factors: List[str] = []

        if gis.heritage_zone:
            zoning_score += 40.0
            zoning_factors.append("Site is located within a heritage protection zone.")

        if gis.airport_zone:
            zoning_score += 35.0
            zoning_factors.append("Site lies under an airport flight funnel height restriction zone.")

        # Land use check
        if bld.building_type.upper() not in gis.land_use.upper() and gis.land_use.upper() != "MIXED USE":
            zoning_score += 20.0
            zoning_factors.append(f"Building type ({bld.building_type}) differs from masterplan zone ({gis.land_use}).")

        if not zoning_factors:
            zoning_factors.append("Zoning classification fully compatible with proposed land use.")

        zoning_score = round(min(100.0, zoning_score), 2)
        zoning_risk = DimensionRisk(
            dimension_name="Zoning & Spatial Risk",
            risk_score=zoning_score,
            risk_level=_score_to_level(zoning_score),
            key_factors=zoning_factors,
        )

        # ── 3. Structural Risk ────────────────────────────────────────────────
        struct_score = 0.0
        struct_factors: List[str] = []

        if bld.height > 15.0:
            struct_score += 25.0
            struct_factors.append(f"High-rise structure ({bld.height} m height > 15 m).")

        if gis.airport_height_limit is not None and bld.height > gis.airport_height_limit:
            struct_score += 50.0
            struct_factors.append(
                f"Building height ({bld.height} m) exceeds airport limit ({gis.airport_height_limit} m)."
            )

        if bld.fsi > 2.0:
            struct_score += 25.0
            struct_factors.append(f"High FSI intensity ({bld.fsi:.2f} > 2.0).")

        if bld.ground_coverage > 60.0:
            struct_score += 20.0
            struct_factors.append(f"High ground coverage ({bld.ground_coverage:.1f}% > 60%).")

        if not struct_factors:
            struct_factors.append("Structural height, FSI, and ground coverage are within standard limits.")

        struct_score = round(min(100.0, struct_score), 2)
        struct_risk = DimensionRisk(
            dimension_name="Structural & Dimensional Risk",
            risk_score=struct_score,
            risk_level=_score_to_level(struct_score),
            key_factors=struct_factors,
        )

        # ── 4. Compliance Risk ────────────────────────────────────────────────
        comp_score = 0.0
        comp_factors: List[str] = []

        if cmp.blocking > 0:
            comp_score += 50.0
            comp_factors.append(f"Presence of {cmp.blocking} BLOCKING violation(s).")

        if cmp.failed > 0:
            comp_score += min(40.0, cmp.failed * 15.0)
            comp_factors.append(f"{cmp.failed} rule evaluation failure(s).")

        deficit = max(0.0, 100.0 - cmp.score) * 0.3
        comp_score += deficit

        if not comp_factors:
            comp_factors.append("Zero compliance failures or blocking violations.")

        comp_score = round(min(100.0, comp_score), 2)
        compliance_risk = DimensionRisk(
            dimension_name="Compliance Violation Risk",
            risk_score=comp_score,
            risk_level=_score_to_level(comp_score),
            key_factors=comp_factors,
        )

        # ── Composite Risk ────────────────────────────────────────────────────
        all_risks = [env_risk, zoning_risk, struct_risk, compliance_risk]
        overall_score = round(sum(r.risk_score for r in all_risks) / 4.0, 2)
        
        # Overall risk level is highest level among dimensions
        highest_level = max(all_risks, key=lambda r: _LEVEL_RANK[r.risk_level]).risk_level

        return RiskAssessment(
            report_id=bundle.report_id,
            overall_risk_score=overall_score,
            overall_risk_level=highest_level,
            environmental_risk=env_risk,
            zoning_risk=zoning_risk,
            structural_risk=struct_risk,
            compliance_risk=compliance_risk,
        )
