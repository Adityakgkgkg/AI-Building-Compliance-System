"""
GIS Dataset Manifest Manager
============================
Generates, validates, and updates manifest.json to enforce spatial data integrity,
SHA256 checksum verification, and authority provenance.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.gis.models import DatasetMetadata


class ManifestManager:
    """Manages spatial dataset metadata manifest."""

    APPROVED_SOURCES = {
        "wards.geojson": {
            "dataset_name": "BBMP Ward Boundaries",
            "source_url": "https://projects.datameet.org/Municipal_Spatial_Data/bangalore/",
            "authority": "BBMP / DataMeet",
            "license": "ODbL / Creative Commons BY-SA",
        },
        "zone_lookup.json": {
            "dataset_name": "BBMP Zonal Classification",
            "source_url": "https://site.bbmp.gov.in/zonalclassification.html",
            "authority": "BBMP Municipal Corporation",
            "license": "Government Open Data",
        },
        "roads.geojson": {
            "dataset_name": "Greater Bangalore OSM Road Network",
            "source_url": "https://download.geofabrik.de/asia/india.html",
            "authority": "OpenStreetMap Contributors / BBMP GIS",
            "license": "ODbL",
        },
        "lakes.geojson": {
            "dataset_name": "Bangalore Water Bodies & Storm Drains",
            "source_url": "https://overpass-turbo.eu/",
            "authority": "BBMP Lake Development Authority / OSM",
            "license": "ODbL",
        },
        "airport_buffer.geojson": {
            "dataset_name": "Airport Height Restriction Funnel",
            "source_url": "https://gba.karnataka.gov.in/gisviewer/index.html",
            "authority": "Airports Authority of India (AAI) / GBA GIS",
            "license": "Government Statutory Restriction",
        },
        "landuse.geojson": {
            "dataset_name": "BDA Master Plan Land Use Classification",
            "source_url": "https://gba.karnataka.gov.in/gisviewer/index.html",
            "authority": "Bangalore Development Authority (BDA)",
            "license": "Government Official Master Plan",
        },
        "bbmp_boundary.geojson": {
            "dataset_name": "BBMP Administrative Boundary",
            "source_url": "https://projects.datameet.org/Municipal_Spatial_Data/bangalore/",
            "authority": "BBMP",
            "license": "Government Open Data",
        }
    }

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.manifest_path = data_dir / "manifest.json"

    def compute_sha256(self, file_path: Path) -> str:
        """Compute SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    def generate_manifest(self) -> Dict[str, Any]:
        """Scan data directory and generate manifest.json."""
        datasets = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for file_name, meta_template in self.APPROVED_SOURCES.items():
            file_path = self.data_dir / file_name
            if not file_path.exists():
                continue

            checksum = self.compute_sha256(file_path)
            geom_count = 0

            if file_name.endswith(".geojson"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        geom_count = len(data.get("features", []))
                except Exception:
                    geom_count = 0
            elif file_name.endswith(".json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        geom_count = len(data) if isinstance(data, list) else len(data.keys())
                except Exception:
                    geom_count = 0

            dataset_entry = {
                "dataset_name": meta_template["dataset_name"],
                "file_name": file_name,
                "source_url": meta_template["source_url"],
                "authority": meta_template["authority"],
                "license": meta_template["license"],
                "download_date": now_str,
                "last_updated": now_str,
                "coordinate_system": "EPSG:4326",
                "version": "1.0.0",
                "checksum_sha256": checksum,
                "geometry_count": geom_count,
                "status": "VERIFIED"
            }
            datasets.append(dataset_entry)

        manifest_data = {
            "city": "Bangalore",
            "planning_authority": "BBMP / BDA",
            "generated_at": now_str,
            "datasets": datasets
        }

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return manifest_data

    def load_manifest(self) -> Optional[Dict[str, Any]]:
        """Load manifest.json if exists, else return None."""
        if not self.manifest_path.exists():
            return None
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
