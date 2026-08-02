"""
MCRDSE Module 2 – Compliance Rule Engine Service
================================================
Evaluates canonical BuildingEvidence and GISEvidence against statutory BBMP municipal
building bye-laws and urban planning regulations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass(frozen=True)
class RawRuleResult:
    """Raw rule evaluation item returned by ComplianceEngineService."""

    rule_id: str
    rule_name: str
    status: str
    severity: str
    expected: str
    actual: str
    difference: str
    message: str
    clause: str
    reference: str
    recommendation: str


@dataclass(frozen=True)
class ComplianceEngineResult:
    """Aggregated compliance engine evaluation result."""

    rules_checked: int
    passed: int
    failed: int
    warnings: int
    blocking: int
    score: float
    rule_results: List[RawRuleResult] = field(default_factory=list)


class ComplianceEngineService:
    """
    Municipal Statutory Compliance Rule Engine.
    """

    @classmethod
    def evaluate(cls, building_ev: Any, gis_ev: Any) -> ComplianceEngineResult:
        """
        Evaluate building and GIS evidence against municipal bye-laws.

        Parameters
        ----------
        building_ev:
            BuildingEvidence object.
        gis_ev:
            GISEvidence object.

        Returns
        -------
        ComplianceEngineResult
        """
        results: List[RawRuleResult] = []

        # ── 1. FSI Limit Check ────────────────────────────────────────────────
        fsi = getattr(building_ev, "fsi", 1.8)
        road_width = getattr(gis_ev, "road_width", 12.0)

        # Max permitted FSI based on road width
        max_fsi = 2.25 if road_width >= 12.0 else 1.75
        if fsi <= max_fsi:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-FSI-001",
                    rule_name="Floor Space Index (FSI) Limit Check",
                    status="PASSED",
                    severity="MAJOR",
                    expected=f"≤ {max_fsi:.2f}",
                    actual=f"{fsi:.2f}",
                    difference="0",
                    message=f"FSI of {fsi:.2f} complies with BBMP Bye-law 7.3.2 for road width {road_width} m.",
                    clause="BBMP Bye-law 7.3.2",
                    reference="BBMP Building Bye-laws 2024, §7.3",
                    recommendation="No corrective action required.",
                )
            )
        else:
            diff = fsi - max_fsi
            results.append(
                RawRuleResult(
                    rule_id="BBMP-FSI-001",
                    rule_name="Floor Space Index (FSI) Limit Check",
                    status="FAILED",
                    severity="BLOCKING",
                    expected=f"≤ {max_fsi:.2f}",
                    actual=f"{fsi:.2f}",
                    difference=f"+{diff:.2f}",
                    message=f"FSI of {fsi:.2f} exceeds maximum permitted limit of {max_fsi:.2f} by {diff:.2f}.",
                    clause="BBMP Bye-law 7.3.2",
                    reference="BBMP Building Bye-laws 2024, §7.3",
                    recommendation=f"Reduce total built-up area by {diff * getattr(building_ev, 'plot_area', 500.0):.1f} m² to achieve FSI ≤ {max_fsi:.2f}.",
                )
            )

        # ── 2. Ground Coverage Check ──────────────────────────────────────────
        coverage = getattr(building_ev, "ground_coverage", 40.0)
        max_coverage = 60.0
        if coverage <= max_coverage:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-COV-001",
                    rule_name="Ground Coverage Limit Check",
                    status="PASSED",
                    severity="MAJOR",
                    expected=f"≤ {max_coverage:.1f}%",
                    actual=f"{coverage:.1f}%",
                    difference="0",
                    message=f"Ground coverage of {coverage:.1f}% is within maximum permitted limit of {max_coverage:.1f}%.",
                    clause="BBMP Bye-law 7.4.1",
                    reference="BBMP Building Bye-laws 2024, §7.4",
                    recommendation="No corrective action required.",
                )
            )
        else:
            diff_cov = coverage - max_coverage
            results.append(
                RawRuleResult(
                    rule_id="BBMP-COV-001",
                    rule_name="Ground Coverage Limit Check",
                    status="FAILED",
                    severity="MAJOR",
                    expected=f"≤ {max_coverage:.1f}%",
                    actual=f"{coverage:.1f}%",
                    difference=f"+{diff_cov:.1f}%",
                    message=f"Ground coverage of {coverage:.1f}% exceeds maximum limit of {max_coverage:.1f}%.",
                    clause="BBMP Bye-law 7.4.1",
                    reference="BBMP Building Bye-laws 2024, §7.4",
                    recommendation=f"Reduce ground floor footprint coverage by {diff_cov:.1f}% of plot area.",
                )
            )

        # ── 3. Height & High-Rise Threshold Check ─────────────────────────────
        height = getattr(building_ev, "height", 12.0)
        if height <= 15.0:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-HEIGHT-001",
                    rule_name="Building Height & High-Rise Threshold",
                    status="PASSED",
                    severity="MAJOR",
                    expected="≤ 15.0 m",
                    actual=f"{height:.1f} m",
                    difference="0",
                    message=f"Building height of {height:.1f} m is below high-rise threshold of 15.0 m.",
                    clause="BBMP Bye-law 8.1.1",
                    reference="BBMP Building Bye-laws 2024, §8.1",
                    recommendation="No corrective action required.",
                )
            )
        else:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-HEIGHT-001",
                    rule_name="Building Height & High-Rise Threshold",
                    status="WARNING",
                    severity="MINOR",
                    expected="≤ 15.0 m",
                    actual=f"{height:.1f} m",
                    difference=f"+{height - 15.0:.1f} m",
                    message=f"Building height of {height:.1f} m classifies as high-rise (> 15.0 m); mandatory Fire Department NOC required.",
                    clause="BBMP Bye-law 8.1.1",
                    reference="BBMP Building Bye-laws 2024, §8.1",
                    recommendation="Obtain Fire Force NOC and install mandatory dual staircase emergency exits.",
                )
            )

        # ── 4. Lake Buffer Zone Protection Check ──────────────────────────────
        lake_buffer = getattr(gis_ev, "lake_buffer", False)
        lake_distance = getattr(gis_ev, "lake_distance", 500.0)

        if not lake_buffer:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-LAKE-001",
                    rule_name="Lake Buffer Zone Protection Check",
                    status="PASSED",
                    severity="BLOCKING",
                    expected="Outside 30m/75m buffer",
                    actual=f"{lake_distance:.0f} m clear distance",
                    difference="0",
                    message=f"Site is located {lake_distance:.0f} m from nearest water body, outside regulated buffer zone.",
                    clause="KMC Act 1976 / NGT Buffer Directive",
                    reference="BDA Revised Master Plan 2031, Zoning Regulation 4.2",
                    recommendation="No corrective action required.",
                )
            )
        else:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-LAKE-001",
                    rule_name="Lake Buffer Zone Protection Check",
                    status="FAILED",
                    severity="BLOCKING",
                    expected="Outside 30m/75m buffer",
                    actual=f"{lake_distance:.0f} m inside buffer",
                    difference="PROHIBITED ZONE",
                    message=f"Site falls within regulated lake buffer zone ({lake_distance:.0f} m). Statutory construction prohibited.",
                    clause="KMC Act 1976 / NGT Buffer Directive",
                    reference="BDA Revised Master Plan 2031, Zoning Regulation 4.2",
                    recommendation="Realign site boundary outside 30 m buffer zone or obtain KPCB / NGT clearance.",
                )
            )

        # ── 5. Airport Funnel Height Limit Check ──────────────────────────────
        airport_zone = getattr(gis_ev, "airport_zone", False)
        airport_limit = getattr(gis_ev, "airport_height_limit", None)

        if not airport_zone or airport_limit is None or height <= airport_limit:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-AIRPORT-001",
                    rule_name="Airport Flight Funnel Height Restriction",
                    status="PASSED",
                    severity="MAJOR",
                    expected=f"≤ {airport_limit or 'Unlimited'} m",
                    actual=f"{height:.1f} m",
                    difference="0",
                    message="Building height is fully compliant with AAI airport height funnel restrictions.",
                    clause="AAI NOC Regulations 2020",
                    reference="Ministry of Civil Aviation GSR 751(E)",
                    recommendation="No corrective action required.",
                )
            )
        else:
            results.append(
                RawRuleResult(
                    rule_id="BBMP-AIRPORT-001",
                    rule_name="Airport Flight Funnel Height Restriction",
                    status="FAILED",
                    severity="BLOCKING",
                    expected=f"≤ {airport_limit:.1f} m",
                    actual=f"{height:.1f} m",
                    difference=f"+{height - airport_limit:.1f} m",
                    message=f"Building height ({height:.1f} m) exceeds AAI flight funnel limitation ({airport_limit:.1f} m).",
                    clause="AAI NOC Regulations 2020",
                    reference="Ministry of Civil Aviation GSR 751(E)",
                    recommendation=f"Reduce upper floor height by {height - airport_limit:.1f} m or apply for AAI Aeronautical Study clearance.",
                )
            )

        # Compute summary metrics
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASSED")
        failed = sum(1 for r in results if r.status == "FAILED")
        warnings = sum(1 for r in results if r.status == "WARNING")
        blocking = sum(1 for r in results if r.severity == "BLOCKING" and r.status == "FAILED")

        score = round((passed / max(1, total)) * 100.0, 1)

        return ComplianceEngineResult(
            rules_checked=total,
            passed=passed,
            failed=failed,
            warnings=warnings,
            blocking=blocking,
            score=score,
            rule_results=results,
        )
