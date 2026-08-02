"""
GIS Dataset Manager & Cache Initialization
==========================================
Loads, validates, repairs, and indexes all official Bangalore GIS GeoJSON layers on app startup.
Guarantees memory caching and zero O(N) spatial lookup latency during execution.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from app.gis.models import GISFeature, DatasetMetadata
from app.gis.geometry import geojson_to_shapely, repair_geometry
from app.gis.spatial_index import SpatialIndex
from app.gis.manifest import ManifestManager

logger = logging.getLogger("app.gis.dataset_manager")


class DatasetManager:
    """Singleton Manager for loading, repairing, and indexing spatial datasets."""
    
    _instance: Optional['DatasetManager'] = None

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
            data_dir = base_dir / "data" / "bangalore"
        
        self.data_dir = data_dir
        self.spatial_indexes: Dict[str, SpatialIndex] = {}
        self.raw_features: Dict[str, List[GISFeature]] = {}
        self.raw_geojson: Dict[str, Dict[str, Any]] = {}
        self.zone_lookup: Dict[str, str] = {}
        self.manifest_data: Optional[Dict[str, Any]] = None
        self.is_loaded: bool = False

    @classmethod
    def get_instance(cls, data_dir: Optional[Path] = None) -> 'DatasetManager':
        if cls._instance is None:
            cls._instance = DatasetManager(data_dir)
        return cls._instance

    def initialize(self) -> None:
        """Load datasets, repair geometries, build spatial indexes."""
        if self.is_loaded:
            return

        logger.info(f"Initializing GIS DatasetManager from {self.data_dir}...")

        if not (self.data_dir / "wards.geojson").exists():
            from app.gis.prepare_datasets import prepare_all_datasets
            prepare_all_datasets()

        # Load Manifest
        manifest_mgr = ManifestManager(self.data_dir)
        self.manifest_data = manifest_mgr.load_manifest() or manifest_mgr.generate_manifest()

        # Load Zone Lookup
        zone_lookup_path = self.data_dir / "zone_lookup.json"
        if zone_lookup_path.exists():
            with open(zone_lookup_path, "r", encoding="utf-8") as f:
                self.zone_lookup = json.load(f)

        # Load GeoJSON Layers
        layers = [
            ("bbmp_boundary", "bbmp_boundary.geojson"),
            ("wards", "wards.geojson"),
            ("roads", "roads.geojson"),
            ("lakes", "lakes.geojson"),
            ("airport_buffer", "airport_buffer.geojson"),
            ("landuse", "landuse.geojson"),
        ]

        for layer_key, file_name in layers:
            file_path = self.data_dir / file_name
            if not file_path.exists():
                logger.warning(f"Spatial layer file {file_name} missing.")
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    geojson_dict = json.load(f)
                    self.raw_geojson[layer_key] = geojson_dict

                features_list: List[GISFeature] = []
                raw_feats = geojson_dict.get("features", [])
                
                for idx, feat_dict in enumerate(raw_feats):
                    properties = feat_dict.get("properties", {})
                    feat_id = str(feat_dict.get("id", f"{layer_key}_{idx}"))
                    
                    try:
                        geom = geojson_to_shapely(feat_dict)
                        geom = repair_geometry(geom)
                        if geom and not geom.is_empty:
                            gis_feat = GISFeature(
                                feature_id=feat_id,
                                geometry=geom,
                                properties=properties,
                                dataset_name=layer_key
                            )
                            features_list.append(gis_feat)
                    except Exception as e:
                        logger.error(f"Failed to parse feature {feat_id} in {file_name}: {e}")

                self.raw_features[layer_key] = features_list
                self.spatial_indexes[layer_key] = SpatialIndex(layer_key, features_list)
                logger.info(f"Indexed layer '{layer_key}' ({len(features_list)} features)")

            except Exception as exc:
                logger.error(f"Error loading layer {file_name}: {exc}")

        self.is_loaded = True
        logger.info("GIS DatasetManager initialization complete.")

    def get_index(self, layer_name: str) -> Optional[SpatialIndex]:
        """Retrieve STRtree spatial index for a dataset layer."""
        if not self.is_loaded:
            self.initialize()
        return self.spatial_indexes.get(layer_name)

    def get_raw_geojson(self, layer_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve raw GeoJSON dictionary for frontend map rendering."""
        if not self.is_loaded:
            self.initialize()
        return self.raw_geojson.get(layer_name)
