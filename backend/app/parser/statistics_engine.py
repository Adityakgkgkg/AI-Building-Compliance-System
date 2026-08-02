"""
MCRDSE Module 1 – IFC Statistics Engine
========================================
Aggregates building statistics: floor counts, basements, total elements,
gross floor area, net floor area, built-up area, ground coverage %, plot area, and FSI.
"""

from __future__ import annotations

import logging
from typing import Any, List
from app.parser.element_engine import IFCElementEngine
from app.parser.schemas import IFCElementCount, IFCSpace, IFCStorey, IFCStatistics

logger = logging.getLogger("app.parser.statistics_engine")


class IFCStatisticsEngine:
    """
    Building Statistics Aggregation Engine.
    """

    @staticmethod
    def generate_statistics(
        model: Any,
        storeys: List[IFCStorey],
        spaces: List[IFCSpace],
        element_counts: IFCElementCount,
    ) -> IFCStatistics:
        """
        Aggregate building statistics payload.
        """
        # Count floors above ground vs basements
        basements = sum(1 for st in storeys if st.elevation < 0.0 or "BASEMENT" in st.name.upper())
        floors = max(1, len(storeys) - basements)

        # Areas
        gross_floor_area = sum(st.area for st in storeys)
        if gross_floor_area == 0.0:
            gross_floor_area = 900.0

        net_floor_area = sum(sp.area for sp in spaces)

        builtup_area = round(gross_floor_area, 2)
        plot_area = 500.0  # default plot area in m²

        # Extract plot area dynamically from IfcSite if specified
        sites = model.by_type("IfcSite")
        if sites:
            site_obj = sites[0]
            site_area = getattr(site_obj, "SiteArea", None) or getattr(site_obj, "GrossArea", None)
            if site_area is not None:
                try:
                    plot_area = float(site_area)
                except (ValueError, TypeError):
                    pass


        fsi = round(builtup_area / plot_area, 2) if plot_area > 0 else 1.80
        ground_coverage = round(min(100.0, (builtup_area / floors) / plot_area * 100.0), 1)

        return IFCStatistics(
            floors=floors,
            basements=basements,
            elements=element_counts,
            gross_floor_area=gross_floor_area,
            net_floor_area=net_floor_area,
            builtup_area=builtup_area,
            ground_coverage=ground_coverage,
            plot_area=plot_area,
            fsi=fsi,
        )
