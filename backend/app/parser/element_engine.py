"""
MCRDSE Module 1 – IFC Element Extraction Engine
================================================
Extracts and counts 17 major IFC element types and indexes entities by native IFC GlobalId
to serve as the foundation for 3D visualization and rule violation highlighting.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
from app.parser.schemas import IFCElementCount

logger = logging.getLogger("app.parser.element_engine")


class IFCElementEngine:
    """
    Element Extraction and GlobalId Indexing Engine.
    """

    @staticmethod
    def extract_element_counts(model: Any) -> IFCElementCount:
        """
        Count occurrences of 17 major IFC entity types.
        """
        walls_count = len(model.by_type("IfcWall")) + len(model.by_type("IfcWallStandardCase"))
        doors_count = len(model.by_type("IfcDoor"))
        windows_count = len(model.by_type("IfcWindow"))
        columns_count = len(model.by_type("IfcColumn"))
        beams_count = len(model.by_type("IfcBeam"))
        slabs_count = len(model.by_type("IfcSlab"))
        roofs_count = len(model.by_type("IfcRoof"))
        footings_count = len(model.by_type("IfcFooting"))
        stairs_count = len(model.by_type("IfcStair"))
        ramps_count = len(model.by_type("IfcRamp"))
        spaces_count = len(model.by_type("IfcSpace"))
        storeys_count = len(model.by_type("IfcBuildingStorey"))
        openings_count = len(model.by_type("IfcOpeningElement"))
        curtain_walls_count = len(model.by_type("IfcCurtainWall"))
        coverings_count = len(model.by_type("IfcCovering"))
        railings_count = len(model.by_type("IfcRailing"))

        total_count = (
            walls_count + doors_count + windows_count + columns_count +
            beams_count + slabs_count + roofs_count + footings_count +
            stairs_count + ramps_count + spaces_count + storeys_count +
            openings_count + curtain_walls_count + coverings_count + railings_count
        )

        return IFCElementCount(
            walls=walls_count,
            doors=doors_count,
            windows=windows_count,
            columns=columns_count,
            beams=beams_count,
            slabs=slabs_count,
            roofs=roofs_count,
            footings=footings_count,
            stairs=stairs_count,
            ramps=ramps_count,
            spaces=spaces_count,
            storeys=storeys_count,
            openings=openings_count,
            curtain_walls=curtain_walls_count,
            coverings=coverings_count,
            railings=railings_count,
            total=total_count,
        )

    @staticmethod
    def index_elements(model: Any) -> Dict[str, dict[str, str]]:
        """
        Build GlobalId lookup table mapping native IFC GlobalIds to entity types and names.
        """
        index: Dict[str, dict[str, str]] = {}
        types = [
            "IfcWall", "IfcWallStandardCase", "IfcDoor", "IfcWindow", "IfcColumn",
            "IfcBeam", "IfcSlab", "IfcRoof", "IfcFooting", "IfcStair", "IfcRamp",
            "IfcSpace", "IfcBuildingStorey", "IfcOpeningElement", "IfcCurtainWall",
            "IfcCovering", "IfcRailing"
        ]

        for t in types:
            for entity in model.by_type(t):
                gid = getattr(entity, "GlobalId", None)
                if gid:
                    index[gid] = {
                        "global_id": gid,
                        "type": entity.is_a(),
                        "name": getattr(entity, "Name", "") or "",
                    }

        return index
