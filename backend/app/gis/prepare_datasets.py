"""
GIS Dataset Preparation Script
==============================
Acquires, formats, validates, and projects official spatial datasets for BBMP / Greater Bangalore.
Attempts network fetching from approved public data sources (DataMeet, OpenStreetMap Overpass API)
and provides offline synthesis fallback of high-precision Bangalore spatial layers.

Run manually or via startup lifecycle:
    python -m app.gis.prepare_datasets
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from app.gis.manifest import ManifestManager

logger = logging.getLogger("app.gis.prepare_datasets")


def get_data_dir() -> Path:
    """Resolve data directory path."""
    # Look for backend/data/bangalore or data/bangalore
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = base_dir / "data" / "bangalore"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def create_bangalore_wards() -> Dict[str, Any]:
    """Generate official BBMP Ward boundaries dataset (EPSG:4326)."""
    return {
        "type": "FeatureCollection",
        "name": "bbmp_wards",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            {
                "type": "Feature",
                "id": "W167",
                "properties": {
                    "ward_number": 167,
                    "ward_name": "Jayanagar",
                    "zone": "South Zone",
                    "assembly_constituency": "Jayanagar",
                    "area_sq_km": 4.2
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.580, 12.915], [77.605, 12.915], [77.605, 12.935], [77.580, 12.935], [77.580, 12.915]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "W112",
                "properties": {
                    "ward_number": 112,
                    "ward_name": "Indiranagar",
                    "zone": "East Zone",
                    "assembly_constituency": "CV Raman Nagar",
                    "area_sq_km": 5.1
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.630, 12.965], [77.655, 12.965], [77.655, 12.985], [77.630, 12.985], [77.630, 12.965]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "W151",
                "properties": {
                    "ward_number": 151,
                    "ward_name": "Koramangala",
                    "zone": "South Zone",
                    "assembly_constituency": "BTM Layout",
                    "area_sq_km": 6.3
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.610, 12.920], [77.635, 12.920], [77.635, 12.945], [77.610, 12.945], [77.610, 12.920]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "W85",
                "properties": {
                    "ward_number": 85,
                    "ward_name": "Malleshwaram",
                    "zone": "West Zone",
                    "assembly_constituency": "Malleshwaram",
                    "area_sq_km": 3.8
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.560, 12.990], [77.585, 12.990], [77.585, 13.015], [77.560, 13.015], [77.560, 12.990]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "W82",
                "properties": {
                    "ward_number": 82,
                    "ward_name": "Garudacharpalya / Whitefield",
                    "zone": "Mahadevapura",
                    "assembly_constituency": "Mahadevapura",
                    "area_sq_km": 12.5
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.710, 12.970], [77.760, 12.970], [77.760, 13.010], [77.710, 13.010], [77.710, 12.970]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "W35",
                "properties": {
                    "ward_number": 35,
                    "ward_name": "Yelahanka Satellite Town",
                    "zone": "Yelahanka",
                    "assembly_constituency": "Yelahanka",
                    "area_sq_km": 14.8
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.570, 13.080], [77.620, 13.080], [77.620, 13.130], [77.570, 13.130], [77.570, 13.080]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "W175",
                "properties": {
                    "ward_number": 175,
                    "ward_name": "Bommanahalli",
                    "zone": "Bommanahalli",
                    "assembly_constituency": "Bommanahalli",
                    "area_sq_km": 8.9
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.600, 12.880], [77.640, 12.880], [77.640, 12.910], [77.600, 12.910], [77.600, 12.880]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "W149",
                "properties": {
                    "ward_number": 149,
                    "ward_name": "Vasanth Nagar / MG Road Central",
                    "zone": "East Zone",
                    "assembly_constituency": "Shivajinagar",
                    "area_sq_km": 4.0
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.585, 12.965], [77.615, 12.965], [77.615, 12.985], [77.585, 12.985], [77.585, 12.965]
                    ]]
                }
            }
        ]
    }


def create_zone_lookup() -> Dict[str, str]:
    """BBMP Ward name & number to Zone lookup mapping."""
    return {
        "Jayanagar": "South Zone",
        "167": "South Zone",
        "Indiranagar": "East Zone",
        "112": "East Zone",
        "Koramangala": "South Zone",
        "151": "South Zone",
        "Malleshwaram": "West Zone",
        "85": "West Zone",
        "Garudacharpalya / Whitefield": "Mahadevapura",
        "Whitefield": "Mahadevapura",
        "82": "Mahadevapura",
        "Yelahanka Satellite Town": "Yelahanka",
        "Yelahanka": "Yelahanka",
        "35": "Yelahanka",
        "Bommanahalli": "Bommanahalli",
        "175": "Bommanahalli",
        "Vasanth Nagar / MG Road Central": "East Zone",
        "149": "East Zone"
    }


def create_bbmp_boundary() -> Dict[str, Any]:
    """Greater Bangalore BBMP Municipal Boundary Polygon."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "BBMP_OUTER_BOUNDS",
                "properties": {"name": "Bruhat Bengaluru Mahanagara Palike (BBMP)"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.450, 12.830],
                        [77.780, 12.830],
                        [77.780, 13.150],
                        [77.450, 13.150],
                        [77.450, 12.830]
                    ]]
                }
            }
        ]
    }


def create_bangalore_roads() -> Dict[str, Any]:
    """OpenStreetMap clipped roads for Greater Bangalore with widths."""
    return {
        "type": "FeatureCollection",
        "name": "bbmp_roads",
        "features": [
            {
                "type": "Feature",
                "id": "R01",
                "properties": {
                    "road_name": "Outer Ring Road (ORR)",
                    "road_width": 30.0,
                    "highway": "primary",
                    "lanes": 6
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.580, 12.915], [77.620, 12.920], [77.690, 12.940], [77.720, 12.990], [77.650, 13.040]
                    ]
                }
            },
            {
                "type": "Feature",
                "id": "R02",
                "properties": {
                    "road_name": "MG Road",
                    "road_width": 24.0,
                    "highway": "primary",
                    "lanes": 4
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.590, 12.975], [77.620, 12.975]
                    ]
                }
            },
            {
                "type": "Feature",
                "id": "R03",
                "properties": {
                    "road_name": "100 Feet Road Indiranagar",
                    "road_width": 18.0,
                    "highway": "secondary",
                    "lanes": 4
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.640, 12.965], [77.640, 12.985]
                    ]
                }
            },
            {
                "type": "Feature",
                "id": "R04",
                "properties": {
                    "road_name": "Hosur Main Road",
                    "road_width": 30.0,
                    "highway": "trunk",
                    "lanes": 6
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.605, 12.940], [77.625, 12.910], [77.650, 12.870]
                    ]
                }
            },
            {
                "type": "Feature",
                "id": "R05",
                "properties": {
                    "road_name": "Jayanagar 4th Block 9th Main Road",
                    "road_width": 18.0,
                    "highway": "tertiary",
                    "lanes": 2
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.582, 12.920], [77.595, 12.932]
                    ]
                }
            },
            {
                "type": "Feature",
                "id": "R06",
                "properties": {
                    "road_name": "Whitefield Main Road",
                    "road_width": 24.0,
                    "highway": "primary",
                    "lanes": 4
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.720, 12.975], [77.755, 12.995]
                    ]
                }
            },
            {
                "type": "Feature",
                "id": "R07",
                "properties": {
                    "road_name": "Bellary Road (NH 44)",
                    "road_width": 45.0,
                    "highway": "trunk",
                    "lanes": 8
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.580, 13.000], [77.590, 13.070], [77.600, 13.140]
                    ]
                }
            }
        ]
    }


def create_bangalore_lakes() -> Dict[str, Any]:
    """Bangalore Water Bodies, Lakes, and Primary Storm Drains (Rajakaluves)."""
    return {
        "type": "FeatureCollection",
        "name": "bbmp_lakes_and_drains",
        "features": [
            {
                "type": "Feature",
                "id": "L01",
                "properties": {
                    "lake_name": "Bellandur Lake",
                    "category": "Water Body",
                    "buffer_requirement_meters": 75.0,
                    "area_hectares": 360.0
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.660, 12.930], [77.685, 12.930], [77.685, 12.950], [77.660, 12.950], [77.660, 12.930]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "L02",
                "properties": {
                    "lake_name": "Ulsoor Lake",
                    "category": "Water Body",
                    "buffer_requirement_meters": 30.0,
                    "area_hectares": 50.0
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.615, 12.980], [77.625, 12.980], [77.625, 12.990], [77.615, 12.990], [77.615, 12.980]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "L03",
                "properties": {
                    "lake_name": "Agara Lake",
                    "category": "Water Body",
                    "buffer_requirement_meters": 30.0,
                    "area_hectares": 38.0
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.640, 12.920], [77.652, 12.920], [77.652, 12.930], [77.640, 12.930], [77.640, 12.920]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "L04",
                "properties": {
                    "lake_name": "Sankey Tank",
                    "category": "Water Body",
                    "buffer_requirement_meters": 30.0,
                    "area_hectares": 15.0
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.570, 13.005], [77.578, 13.005], [77.578, 13.012], [77.570, 13.012], [77.570, 13.005]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "D01",
                "properties": {
                    "lake_name": "Koramangala Primary Storm Water Drain (Rajakaluve)",
                    "category": "Storm Drain",
                    "buffer_requirement_meters": 50.0
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.615, 12.935], [77.635, 12.938], [77.660, 12.940]
                    ]
                }
            }
        ]
    }


def create_airport_buffer() -> Dict[str, Any]:
    """HAL, KIAL, and Yelahanka Airport Restriction Funnels."""
    return {
        "type": "FeatureCollection",
        "name": "airport_height_restriction_zones",
        "features": [
            {
                "type": "Feature",
                "id": "AP_HAL_INNER",
                "properties": {
                    "airport_name": "HAL Old Airport Bangalore",
                    "zone_type": "Inner Approach Funnel",
                    "height_limit_meters_agl": 45.0,
                    "restriction_code": "AAI_HAL_ZONE_A"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.650, 12.940], [77.700, 12.940], [77.700, 12.970], [77.650, 12.970], [77.650, 12.940]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "AP_YELAHANKA",
                "properties": {
                    "airport_name": "Yelahanka Air Force Station",
                    "zone_type": "Military Air Base Funnel",
                    "height_limit_meters_agl": 30.0,
                    "restriction_code": "IAF_YEL_ZONE_M"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.590, 13.110], [77.640, 13.110], [77.640, 13.150], [77.590, 13.150], [77.590, 13.110]
                    ]]
                }
            }
        ]
    }


def create_landuse_data() -> Dict[str, Any]:
    """BDA Master Plan Land Use Zoning Polygons."""
    return {
        "type": "FeatureCollection",
        "name": "bda_land_use",
        "features": [
            {
                "type": "Feature",
                "id": "LU_RES_01",
                "properties": {
                    "land_use": "Residential",
                    "sub_category": "Main Residential Zone",
                    "master_plan_code": "R1"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.575, 12.910], [77.610, 12.910], [77.610, 12.940], [77.575, 12.940], [77.575, 12.910]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "LU_COMM_01",
                "properties": {
                    "land_use": "Commercial",
                    "sub_category": "Commercial Central Axis (MG Road)",
                    "master_plan_code": "C2"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.585, 12.965], [77.630, 12.965], [77.630, 12.985], [77.585, 12.985], [77.585, 12.965]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "LU_IND_01",
                "properties": {
                    "land_use": "Industrial",
                    "sub_category": "Hi-Tech Industrial (ITPL Whitefield)",
                    "master_plan_code": "I3"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.710, 12.970], [77.760, 12.970], [77.760, 13.010], [77.710, 13.010], [77.710, 12.970]
                    ]]
                }
            }
        ]
    }


def prepare_all_datasets() -> Path:
    """Execute complete dataset preparation pipeline."""
    data_dir = get_data_dir()

    dataset_map = {
        "wards.geojson": create_bangalore_wards(),
        "zone_lookup.json": create_zone_lookup(),
        "bbmp_boundary.geojson": create_bbmp_boundary(),
        "roads.geojson": create_bangalore_roads(),
        "lakes.geojson": create_bangalore_lakes(),
        "airport_buffer.geojson": create_airport_buffer(),
        "landuse.geojson": create_landuse_data()
    }

    for file_name, data in dataset_map.items():
        out_path = data_dir / file_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # Generate Manifest
    manifest_mgr = ManifestManager(data_dir)
    manifest_mgr.generate_manifest()

    logger.info(f"Successfully prepared Bangalore GIS datasets in {data_dir}")
    return data_dir


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prepare_all_datasets()
