"""
AI Building Compliance System — IFC Parser Utilities

IFC-specific helper functions used by the extractor modules.
All geometry extraction is wrapped in broad exception guards so
that a missing or invalid 3D representation never crashes the pipeline.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Safe attribute access ─────────────────────────────────────────

def safe_get(obj: Any, *attrs: str, default: Any = None) -> Any:
    """
    Safely traverse a chain of attributes on an IfcOpenShell object.

    Examples:
        safe_get(ifc_project, "Name")          → project name or None
        safe_get(ifc_project, "OwnerHistory", "OwningOrganization", "Name")

    Args:
        obj:     The root IfcOpenShell entity.
        *attrs:  Attribute names to traverse in order.
        default: Value returned if any step is None or raises.

    Returns:
        The resolved attribute value, or *default* on any failure.
    """
    current = obj
    for attr in attrs:
        if current is None:
            return default
        try:
            current = getattr(current, attr, default)
        except Exception:
            return default
    return current if current is not None else default


# ── Unit extraction ───────────────────────────────────────────────

def get_length_unit(ifc_model: Any) -> Optional[str]:
    """
    Extract the primary length unit name from IfcUnitAssignment.

    Returns the unit name (e.g. 'METRE', 'MILLIMETRE') or None.
    """
    try:
        units = ifc_model.by_type("IfcUnitAssignment")
        if not units:
            return None
        unit_assignment = units[0]
        for unit in unit_assignment.Units:
            unit_type = getattr(unit, "UnitType", None)
            if unit_type == "LENGTHUNIT":
                name = getattr(unit, "Name", None)
                prefix = getattr(unit, "Prefix", None)
                if prefix:
                    return f"{prefix}{name}"
                return name
    except Exception as exc:
        logger.debug("Could not extract length unit: %s", exc)
    return None


def get_unit_scale(ifc_model: Any) -> float:
    """
    Return a multiplier to convert IFC length values to metres.

    Handles common cases: METRE (1.0), MILLIMETRE (0.001),
    CENTIMETRE (0.01), FOOT (0.3048), INCH (0.0254).
    Defaults to 1.0 (assumes metres) on unknown units.
    """
    unit_name = get_length_unit(ifc_model) or ""
    scale_map: dict[str, float] = {
        "METRE": 1.0,
        "MILLIMETRE": 0.001,
        "CENTIMETRE": 0.01,
        "FOOT": 0.3048,
        "INCH": 0.0254,
    }
    return scale_map.get(unit_name.upper(), 1.0)


def ifc_length_to_metres(value: float, scale: float) -> float:
    """Convert a raw IFC length value to metres using *scale*."""
    return round(value * scale, 4)


# ── Storey height extraction ──────────────────────────────────────

def extract_storey_elevations(ifc_model: Any) -> Optional[list[float]]:
    """
    Extract elevation (Z) of each IfcBuildingStorey, sorted ascending.

    Returns a list of elevations in metres, or None if unavailable.
    """
    try:
        storeys = ifc_model.by_type("IfcBuildingStorey")
        if not storeys:
            return None
        scale = get_unit_scale(ifc_model)
        elevations: list[float] = []
        for storey in storeys:
            elev = getattr(storey, "Elevation", None)
            if elev is not None:
                elevations.append(ifc_length_to_metres(float(elev), scale))
        if not elevations:
            return None
        return sorted(elevations)
    except Exception as exc:
        logger.debug("Could not extract storey elevations: %s", exc)
        return None


# ── Geometry extraction ───────────────────────────────────────────

def extract_geometry(ifc_model: Any) -> dict:
    """
    Attempt to extract geometric properties using IfcOpenShell.

    All computation is wrapped in try/except. If geometry is
    unavailable (e.g. the IFC contains no 3D representation),
    each field is set to None rather than raising an exception.

    Returns a dict matching GeometryInfo fields:
        gross_floor_area, height, storey_heights, footprint, bounding_box
    """
    result: dict = {
        "gross_floor_area": None,
        "height": None,
        "storey_heights": None,
        "footprint": None,
        "bounding_box": None,
    }

    # ── Storey heights (from elevations) ─────────────────────────
    try:
        elevations = extract_storey_elevations(ifc_model)
        if elevations and len(elevations) > 1:
            heights = [
                round(elevations[i + 1] - elevations[i], 4)
                for i in range(len(elevations) - 1)
            ]
            result["storey_heights"] = heights
        elif elevations:
            result["storey_heights"] = elevations
    except Exception as exc:
        logger.debug("Storey height computation failed: %s", exc)

    # ── Gross floor area (sum of IfcSpace NetFloorArea properties) ─
    try:
        total_area: float = 0.0
        found_area = False
        spaces = ifc_model.by_type("IfcSpace")
        for space in spaces:
            for definition in (getattr(space, "IsDefinedBy", None) or []):
                relating = getattr(definition, "RelatingPropertyDefinition", None)
                if relating is None:
                    continue
                props = getattr(relating, "HasProperties", None) or []
                for prop in props:
                    prop_name = getattr(prop, "Name", "")
                    if prop_name in ("NetFloorArea", "GrossFloorArea", "Area"):
                        val = getattr(prop, "NominalValue", None)
                        if val is not None:
                            num = getattr(val, "wrappedValue", None)
                            if num is not None:
                                total_area += float(num)
                                found_area = True
        if found_area:
            scale = get_unit_scale(ifc_model)
            # Area scale = length_scale²
            result["gross_floor_area"] = round(total_area * scale * scale, 4)
    except Exception as exc:
        logger.debug("Gross floor area extraction failed: %s", exc)

    # ── Bounding box & height (via ifcopenshell.geom) ─────────────
    try:
        import ifcopenshell.geom as geom  # noqa: PLC0415

        settings = geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")
        found_geom = False

        iterator = geom.iterator(settings, ifc_model)
        if iterator.initialize():
            while True:
                shape = iterator.get()
                verts = shape.geometry.verts  # flat [x,y,z, x,y,z, ...]
                for i in range(0, len(verts), 3):
                    x, y, z = verts[i], verts[i + 1], verts[i + 2]
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    min_z = min(min_z, z)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    max_z = max(max_z, z)
                    found_geom = True
                if not iterator.next():
                    break

        if found_geom:
            scale = get_unit_scale(ifc_model)
            result["bounding_box"] = {
                "min_x": round(min_x * scale, 4),
                "min_y": round(min_y * scale, 4),
                "min_z": round(min_z * scale, 4),
                "max_x": round(max_x * scale, 4),
                "max_y": round(max_y * scale, 4),
                "max_z": round(max_z * scale, 4),
            }
            result["height"] = round((max_z - min_z) * scale, 4)
            result["footprint"] = round(
                (max_x - min_x) * (max_y - min_y) * scale * scale, 4
            )
    except ImportError:
        logger.debug("ifcopenshell.geom not available; skipping bounding box.")
    except Exception as exc:
        logger.debug("Geometry kernel extraction failed: %s", exc)

    return result
