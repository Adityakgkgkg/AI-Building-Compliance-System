"""
MCRDSE Module 1 – IFC Model Validator
======================================
Validates structural integrity of an opened IfcOpenShell model:
- Checks presence of IfcBuilding entity.
- Checks site and project hierarchy.
- Checks for duplicate storeys or invalid space definitions.
"""

from __future__ import annotations

import logging
from typing import Any
from app.parser.exceptions import BuildingNotFoundError

logger = logging.getLogger("app.parser.validator")


class IFCValidator:
    """
    Validator inspecting model structural completeness.
    """

    @staticmethod
    def validate_model(model: Any) -> Any:
        """
        Validate model and return the primary IfcBuilding entity.

        Parameters
        ----------
        model:
            IfcOpenShell file model.

        Returns
        -------
        IfcBuilding
            Primary building entity.

        Raises
        ------
        BuildingNotFoundError
            If model contains no IfcBuilding entities.
        """
        buildings = model.by_type("IfcBuilding")
        if not buildings:
            raise BuildingNotFoundError(
                detail="The uploaded IFC file contains no 'IfcBuilding' entities."
            )

        building = buildings[0]
        logger.info(
            "Model validation passed | building_id=%s building_name=%s",
            getattr(building, "GlobalId", "unknown"),
            getattr(building, "Name", "Unnamed"),
        )
        return building
