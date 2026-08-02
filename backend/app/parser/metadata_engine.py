"""
MCRDSE Module 1 – IFC Metadata Extraction Engine
=================================================
Responsible for extracting building, site, project, occupancy, author,
and application metadata from an IFC model.
"""

from __future__ import annotations

import logging
from typing import Any
from app.parser.schemas import IFCMetadata

logger = logging.getLogger("app.parser.metadata_engine")


class IFCMetadataEngine:
    """
    Extractor for building, project, site, and author metadata.
    """

    @staticmethod
    def extract_metadata(model: Any, building: Any) -> IFCMetadata:
        """
        Extract IFCMetadata payload from model and building entity.
        """
        global_id = getattr(building, "GlobalId", "BLD-UNKNOWN")
        building_name = getattr(building, "Name", None) or "Municipal Building"
        description = getattr(building, "Description", None)
        long_name = getattr(building, "LongName", None)

        # Extract Project name
        projects = model.by_type("IfcProject")
        project_name = getattr(projects[0], "Name", None) if projects else "Municipal Project"
        project_name = project_name or "Municipal Project"

        # Extract Site name
        sites = model.by_type("IfcSite")
        site_name = getattr(sites[0], "Name", None) if sites else "BBMP Site"
        site_name = site_name or "BBMP Site"

        # Schema version
        schema_version = getattr(model, "schema", "IFC4").upper()

        # Occupancy & Building Type
        building_type = "RESIDENTIAL"
        occupancy = "Residential"

        # Inspect ObjectType or ElementType property sets if available
        obj_type = getattr(building, "ObjectType", None)
        if obj_type:
            obj_upper = str(obj_type).upper()
            if "COMMERCIAL" in obj_upper:
                building_type = "COMMERCIAL"
                occupancy = "Commercial"
            elif "INDUSTRIAL" in obj_upper:
                building_type = "INDUSTRIAL"
                occupancy = "Industrial"
            elif "MIXED" in obj_upper:
                building_type = "MIXED_USE"
                occupancy = "Mixed Use"
            elif "APARTMENT" in obj_upper or "RESIDENTIAL" in obj_upper:
                building_type = "RESIDENTIAL"
                occupancy = "Residential"

        # Extract Owner History & Author details
        author = "BIM Architect"
        organization = "Municipal Design Bureau"
        timestamp = "2026-01-01T00:00:00Z"
        application = "BIM Authoring Platform"
        owner_hist_str = None

        owners = model.by_type("IfcOwnerHistory")
        if owners:
            ow = owners[0]
            owner_hist_str = f"OwnerHistory-{getattr(ow, 'GlobalId', '0')}"

            owning_user = getattr(ow, "OwningUser", None)
            if owning_user:
                person = getattr(owning_user, "ThePerson", None)
                if person:
                    fn = getattr(person, "GivenName", "") or ""
                    ln = getattr(person, "FamilyName", "") or ""
                    if fn or ln:
                        author = f"{fn} {ln}".strip()

                org = getattr(owning_user, "TheOrganization", None)
                if org:
                    organization = getattr(org, "Name", None) or organization

            owning_app = getattr(ow, "OwningApplication", None)
            if owning_app:
                application = getattr(owning_app, "ApplicationFullName", None) or getattr(owning_app, "ApplicationIdentifier", None) or application

            creation_date = getattr(ow, "CreationDate", None)
            if creation_date:
                timestamp = str(creation_date)

        return IFCMetadata(
            global_id=global_id,
            building_name=building_name,
            project_name=project_name,
            site_name=site_name,
            building_type=building_type,
            occupancy=occupancy,
            description=description,
            long_name=long_name,
            schema_version=schema_version,
            author=author,
            organization=organization,
            timestamp=timestamp,
            application=application,
            owner_history=owner_hist_str,
        )
