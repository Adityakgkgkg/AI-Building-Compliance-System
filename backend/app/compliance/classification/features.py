"""
AI Building Compliance System — Building Features Extractor

Extracts structured feature signals from a raw ParseResult dict.
Features are used by the heuristic classifier (Stage 1).

Feature extraction is purely functional — no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BuildingFeatures:
    """
    Structured set of signals extracted from a ParseResult.

    All fields are nullable — missing data is tolerated gracefully.
    """

    # ── Metadata text (used for keyword matching in Priority 1) ───
    project_name: Optional[str] = None
    building_name: Optional[str] = None
    description: Optional[str] = None

    # ── Quantitative geometry ─────────────────────────────────────
    storeys: int = 0
    height: Optional[float] = None          # m
    footprint: Optional[float] = None       # sqm
    gross_floor_area: Optional[float] = None  # sqm

    # ── Element counts ────────────────────────────────────────────
    walls: int = 0
    doors: int = 0
    windows: int = 0
    stairs: int = 0
    spaces: int = 0
    columns: int = 0
    roofs: int = 0
    slabs: int = 0

    # ── Caller-supplied signals ───────────────────────────────────
    num_units: Optional[int] = None
    num_bedrooms: Optional[int] = None
    num_kitchens: Optional[int] = None
    num_shops: Optional[int] = None
    num_offices: Optional[int] = None
    has_lift: Optional[bool] = None
    has_basement: Optional[bool] = None
    has_loading_dock: Optional[bool] = None
    factory_floor_area: Optional[float] = None
    building_use: Optional[str] = None
    building_description: Optional[str] = None

    # ── Derived boolean signals ───────────────────────────────────
    is_high_rise: bool = False      # storeys > 4
    is_large_footprint: bool = False  # footprint > 500 sqm
    is_multi_storey: bool = False   # storeys >= 3
    has_many_spaces: bool = False   # spaces > 20
    has_many_stairs: bool = False   # stairs > 2
    has_many_doors: bool = False    # doors > 30

    # ── Combined metadata texts ───────────────────────────────────
    @property
    def all_text(self) -> str:
        """Return all metadata text concatenated and lowercased for keyword scanning."""
        parts: List[str] = []
        for val in [
            self.project_name,
            self.building_name,
            self.description,
            self.building_use,
            self.building_description,
        ]:
            if val:
                parts.append(val.lower())
        return " ".join(parts)


def extract_features(
    parse_data: Dict[str, Any],
    building_params: Optional[Any] = None,  # BuildingParams
) -> BuildingFeatures:
    """
    Extract BuildingFeatures from a raw ParseResult dict.

    Args:
        parse_data:       Raw ParseResult dict from the IFC parser.
        building_params:  Optional BuildingParams for supplemental signals.

    Returns:
        BuildingFeatures with all available signals populated.
    """
    building = parse_data.get("building") or {}
    elements = parse_data.get("elements") or {}
    geometry = parse_data.get("geometry") or {}

    raw_storeys = building.get("storeys")
    storeys: int = int(raw_storeys) if raw_storeys is not None else 0
    height: Optional[float] = geometry.get("height")
    footprint: Optional[float] = geometry.get("footprint")
    gfa: Optional[float] = geometry.get("gross_floor_area")
    spaces: int = elements.get("spaces", 0) or 0
    stairs: int = elements.get("stairs", 0) or 0
    doors: int = elements.get("doors", 0) or 0

    # Supplement from caller params
    num_units: Optional[int] = None
    num_bedrooms: Optional[int] = None
    num_kitchens: Optional[int] = None
    num_shops: Optional[int] = None
    num_offices: Optional[int] = None
    has_lift: Optional[bool] = None
    has_basement: Optional[bool] = None
    has_loading_dock: Optional[bool] = None
    factory_floor_area: Optional[float] = None
    building_use: Optional[str] = None
    building_description: Optional[str] = None

    if building_params is not None:
        num_units = getattr(building_params, "num_units", None)
        num_bedrooms = getattr(building_params, "num_bedrooms", None)
        num_kitchens = getattr(building_params, "num_kitchens", None)
        num_shops = getattr(building_params, "num_shops", None)
        num_offices = getattr(building_params, "num_offices", None)
        has_lift = getattr(building_params, "has_lift", None)
        has_basement = getattr(building_params, "has_basement", None)
        has_loading_dock = getattr(building_params, "has_loading_dock", None)
        factory_floor_area = getattr(building_params, "factory_floor_area", None)
        building_use = getattr(building_params, "building_use", None)
        building_description = getattr(building_params, "building_description", None)

    return BuildingFeatures(
        project_name=building.get("project_name"),
        building_name=building.get("building_name"),
        description=building.get("description"),
        storeys=storeys,
        height=height,
        footprint=footprint,
        gross_floor_area=gfa,
        walls=elements.get("walls", 0) or 0,
        doors=doors,
        windows=elements.get("windows", 0) or 0,
        stairs=stairs,
        spaces=spaces,
        columns=elements.get("columns", 0) or 0,
        roofs=elements.get("roofs", 0) or 0,
        slabs=elements.get("slabs", 0) or 0,
        num_units=num_units,
        num_bedrooms=num_bedrooms,
        num_kitchens=num_kitchens,
        num_shops=num_shops,
        num_offices=num_offices,
        has_lift=has_lift,
        has_basement=has_basement,
        has_loading_dock=has_loading_dock,
        factory_floor_area=factory_floor_area,
        building_use=building_use,
        building_description=building_description,
        # Derived booleans
        is_high_rise=storeys > 4,
        is_large_footprint=(footprint or 0) > 500,
        is_multi_storey=storeys >= 3,
        has_many_spaces=spaces > 20,
        has_many_stairs=stairs > 2,
        has_many_doors=doors > 30,
    )
