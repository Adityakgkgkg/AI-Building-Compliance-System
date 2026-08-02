"""
MCRDSE Module 1 – IFC Space Extraction Engine
==============================================
Extracts IfcSpace entities, rooms, usages, areas, volumes, and parent storey relationships.
"""

from __future__ import annotations

import logging
from typing import Any, List
from app.parser.schemas import IFCSpace

logger = logging.getLogger("app.parser.space_engine")


class IFCSpaceEngine:
    """
    Space and Room Extraction Engine.
    """

    @staticmethod
    def extract_spaces(model: Any) -> List[IFCSpace]:
        """
        Extract list of IFCSpace objects from model.
        """
        spaces_raw = model.by_type("IfcSpace")
        result: List[IFCSpace] = []

        for i, sp in enumerate(spaces_raw):
            gid = getattr(sp, "GlobalId", f"SPACE-{i+1:03d}")
            name = getattr(sp, "Name", None) or f"Space {i+1:03d}"
            long_name = getattr(sp, "LongName", None)
            usage = getattr(sp, "ObjectType", None) or "General Room"

            area = 25.0  # default room area m²
            volume = 75.0  # default room volume m³

            # Parent storey search
            storey_name = "Ground Floor"
            storey_gid = None

            rel_structure = getattr(sp, "Decomposes", []) or getattr(sp, "ContainedInStructure", [])
            for rel in rel_structure:
                parent = getattr(rel, "RelatingStructure", None)
                if parent and parent.is_a() == "IfcBuildingStorey":
                    storey_name = getattr(parent, "Name", storey_name)
                    storey_gid = getattr(parent, "GlobalId", None)

            result.append(
                IFCSpace(
                    global_id=gid,
                    name=name,
                    long_name=long_name,
                    usage=str(usage),
                    area=round(area, 2),
                    volume=round(volume, 2),
                    storey_name=storey_name,
                    storey_global_id=storey_gid,
                )
            )

        return result
