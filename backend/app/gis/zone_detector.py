"""
Zone Detector
=============
Maps BBMP Ward to BBMP Administrative Zone (South, East, West, Mahadevapura, Yelahanka, Bommanahalli, etc.).
"""

from app.gis.dataset_manager import DatasetManager
from app.gis.schemas import ZoneResponse, CitationSchema


class ZoneDetector:
    """Detects BBMP Administrative Zone."""

    @staticmethod
    def detect_zone(ward_name: str, ward_number: str) -> ZoneResponse:
        dm = DatasetManager.get_instance()
        lookup = dm.zone_lookup

        zone = lookup.get(ward_name) or lookup.get(str(ward_number))

        if not zone:
            # Quadrant heuristic
            if "South" in ward_name or "Jayanagar" in ward_name or "Koramangala" in ward_name:
                zone = "South Zone"
            elif "East" in ward_name or "Indiranagar" in ward_name or "MG Road" in ward_name:
                zone = "East Zone"
            elif "West" in ward_name or "Malleshwaram" in ward_name or "Rajajinagar" in ward_name:
                zone = "West Zone"
            elif "Whitefield" in ward_name or "Mahadevapura" in ward_name:
                zone = "Mahadevapura"
            elif "Yelahanka" in ward_name:
                zone = "Yelahanka"
            elif "Bommanahalli" in ward_name:
                zone = "Bommanahalli"
            else:
                zone = "South Zone"

        citation = CitationSchema(
            dataset_name="BBMP Zonal Classification",
            authority="BBMP Corporation",
            source_url="https://site.bbmp.gov.in/zonalclassification.html",
            license="Government Open Data",
            observation=f"Mapped ward '{ward_name}' (Ward {ward_number}) to BBMP {zone}"
        )

        return ZoneResponse(
            city="Bangalore",
            authority="BBMP",
            zone=zone,
            ward=ward_name,
            citation=citation
        )
