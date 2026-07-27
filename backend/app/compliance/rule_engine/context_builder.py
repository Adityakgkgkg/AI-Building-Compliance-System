"""
AI Building Compliance System — Evaluation Context Builder

Builds a flat EvaluationContext dict from:
  - ParseResult (IFC parser output)
  - BuildingParams (caller-supplied site context)

The EvaluationContext is a plain dict where every key is a field name
that rules can reference directly via their 'field' attribute.

Pre-computed derived fields included:
  far                  — gross_floor_area / plot_area
  ground_coverage_pct  — (footprint / plot_area) * 100
  parking_ratio        — parking_spaces_provided / num_units
  min_storey_height    — min(storey_heights)
  min_side_setback     — min(left_setback, right_setback)
  min_setback          — min(all_setbacks)
  is_high_rise         — storeys > 4
  is_very_high_rise    — height > 24.0 (fire safety trigger)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# High-rise height threshold (m) — used for fire/life safety rule applicability
HIGH_RISE_HEIGHT_THRESHOLD = 15.0   # G+3: 4 storeys
VERY_HIGH_RISE_HEIGHT_THRESHOLD = 24.0  # Requires additional fire safety


def build_context(
    parse_data: Dict[str, Any],
    building_params: Optional[Any] = None,  # BuildingParams Pydantic model
) -> Dict[str, Any]:
    """
    Build and return the flat EvaluationContext dict.

    Args:
        parse_data:      Raw ParseResult dict from the IFC parser.
        building_params: BuildingParams Pydantic model (may be None).

    Returns:
        Flat dict with all available fields and pre-computed derived values.
    """
    building = parse_data.get("building") or {}
    elements = parse_data.get("elements") or {}
    geometry = parse_data.get("geometry") or {}

    # ── Base fields from IFC ParseResult ─────────────────────────
    ctx: Dict[str, Any] = {
        # Building metadata
        "project_name":    building.get("project_name"),
        "building_name":   building.get("building_name"),
        "description":     building.get("description"),
        "ifc_schema":      building.get("ifc_schema"),
        "units":           building.get("units"),
        "storeys":         building.get("storeys") or 0,

        # Element counts
        "walls":    elements.get("walls", 0) or 0,
        "doors":    elements.get("doors", 0) or 0,
        "windows":  elements.get("windows", 0) or 0,
        "slabs":    elements.get("slabs", 0) or 0,
        "columns":  elements.get("columns", 0) or 0,
        "beams":    elements.get("beams", 0) or 0,
        "roofs":    elements.get("roofs", 0) or 0,
        "stairs":   elements.get("stairs", 0) or 0,
        "spaces":   elements.get("spaces", 0) or 0,
        "openings": elements.get("openings", 0) or 0,

        # Geometry
        "gross_floor_area":  geometry.get("gross_floor_area"),
        "height":            geometry.get("height"),
        "footprint":         geometry.get("footprint"),
        "storey_heights":    geometry.get("storey_heights"),
        "bounding_box":      geometry.get("bounding_box"),
    }

    # ── Merge BuildingParams ──────────────────────────────────────
    if building_params is not None:
        bp_dict = (
            building_params.model_dump()
            if hasattr(building_params, "model_dump")
            else building_params
        )
        ctx.update({k: v for k, v in bp_dict.items() if v is not None})

    # ── Compute derived fields ────────────────────────────────────
    _compute_derived(ctx)

    return ctx


def _compute_derived(ctx: Dict[str, Any]) -> None:
    """
    Compute and inject derived fields into the context dict in-place.

    All computations are safe — missing inputs result in None values.
    """
    storeys: int = ctx.get("storeys") or 0
    height: Optional[float] = ctx.get("height")
    gfa: Optional[float] = ctx.get("gross_floor_area")
    footprint: Optional[float] = ctx.get("footprint")
    plot_area: Optional[float] = ctx.get("plot_area")
    storey_heights = ctx.get("storey_heights")
    num_units = ctx.get("num_units")
    parking = ctx.get("parking_spaces_provided")

    front = ctx.get("front_setback")
    rear  = ctx.get("rear_setback")
    left  = ctx.get("left_setback")
    right = ctx.get("right_setback")

    # FAR / FSI
    ctx["far"] = (
        round(gfa / plot_area, 4)
        if gfa is not None and plot_area and plot_area > 0
        else None
    )

    # Ground coverage %
    ctx["ground_coverage_pct"] = (
        round((footprint / plot_area) * 100, 4)
        if footprint is not None and plot_area and plot_area > 0
        else None
    )

    # Parking ratio
    ctx["parking_ratio"] = (
        round(parking / num_units, 4)
        if parking is not None and num_units and num_units > 0
        else None
    )

    # Min storey height
    ctx["min_storey_height"] = (
        min(h for h in storey_heights if h is not None)
        if storey_heights and len(storey_heights) > 0
        else None
    )

    # Setback aggregates
    side_setbacks = [s for s in (left, right) if s is not None]
    all_setbacks = [s for s in (front, rear, left, right) if s is not None]
    ctx["min_side_setback"] = min(side_setbacks) if side_setbacks else None
    ctx["min_setback"] = min(all_setbacks) if all_setbacks else None
    ctx["max_setback"] = max(all_setbacks) if all_setbacks else None

    # High-rise flags
    ctx["is_high_rise"] = storeys > 4
    ctx["is_very_high_rise"] = (height is not None and height > VERY_HIGH_RISE_HEIGHT_THRESHOLD)
    ctx["is_multi_unit"] = (num_units is not None and num_units >= 4)

    # Open space ratio (if available)
    open_space = ctx.get("open_space_area")
    ctx["open_space_ratio"] = (
        round((open_space / plot_area) * 100, 4)
        if open_space is not None and plot_area and plot_area > 0
        else None
    )

    logger.debug(
        "EvaluationContext computed: FAR=%s, coverage=%s%%, is_high_rise=%s",
        ctx["far"],
        ctx["ground_coverage_pct"],
        ctx["is_high_rise"],
    )
