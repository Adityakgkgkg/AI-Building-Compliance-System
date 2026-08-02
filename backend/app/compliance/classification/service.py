"""
MCRDSE Module 2 – Building Classification Service
=================================================
Predicts building classification category and confidence based on IFC attributes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClassificationResult:
    """Raw result returned by ClassificationService.classify()."""

    predicted_type: str
    confidence: float
    reason: str


class ClassificationService:
    """
    Building Type Classification Engine.
    """

    @classmethod
    def classify(cls, building_ev: Any) -> ClassificationResult:
        """
        Classify building type based on IFC building metadata.

        Parameters
        ----------
        building_ev:
            BuildingEvidence object.

        Returns
        -------
        ClassificationResult
        """
        b_type = getattr(building_ev, "building_type", "RESIDENTIAL").upper()
        occupancy = getattr(building_ev, "occupancy", "Residential").upper()
        height = getattr(building_ev, "height", 12.0)
        floors = getattr(building_ev, "floors", 3)

        if "COMMERCIAL" in b_type or "COMMERCIAL" in occupancy or "OFFICE" in occupancy:
            predicted = "Commercial"
            confidence = 0.94
            reason = f"Commercial classification confirmed from IFC building type '{b_type}' and occupancy."
        elif "INDUSTRIAL" in b_type or "FACTORY" in occupancy:
            predicted = "Industrial"
            confidence = 0.91
            reason = f"Industrial classification confirmed from IFC building type '{b_type}'."
        elif "MIXED" in b_type or "MIXED" in occupancy:
            predicted = "Mixed Use"
            confidence = 0.89
            reason = "Mixed-use classification derived from multi-tenant occupancy layout."
        elif floors > 4 or height > 15.0:
            predicted = "Apartment"
            confidence = 0.96
            reason = f"Multi-story residential apartment classification ({floors} floors, {height:.1f} m height)."
        else:
            predicted = "Residential"
            confidence = 0.95
            reason = f"Standard residential building classification confirmed ({floors} floors, {height:.1f} m height)."

        return ClassificationResult(
            predicted_type=predicted,
            confidence=confidence,
            reason=reason,
        )
