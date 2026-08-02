/**
 * GIS Context Intelligence Service Client
 * =======================================
 * Axios API client for evaluating urban context, fetching spatial layers, and loading dataset manifests.
 */

import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Citation {
  dataset_name: string;
  authority: string;
  source_url: string;
  license: string;
  feature_id?: string;
  observation: string;
}

export interface GISContextResponse {
  city: string;
  authority: string;
  zone: string;
  ward: string;
  ward_number?: number;
  road_name: string;
  road_width: number;
  land_use: string;
  lake_distance: number;
  lake_buffer: boolean;
  airport_zone: boolean;
  airport_height_limit?: number | null;
  flood_risk: string;
  heritage_zone: boolean;
  storm_drain_distance: number;
  is_inside_bbmp: boolean;
  approval_report_text: string;
  citations: Citation[];
  execution_time_ms: number;
}

export interface ManifestDataset {
  dataset_name: string;
  file_name: string;
  source_url: string;
  authority: string;
  license: string;
  download_date: string;
  last_updated: string;
  coordinate_system: string;
  version: string;
  checksum_sha256: string;
  geometry_count: number;
  status: string;
}

export interface ManifestData {
  city: string;
  planning_authority: string;
  generated_at: string;
  datasets: ManifestDataset[];
}

export const fetchGISContext = async (
  latitude: number,
  longitude: number
): Promise<GISContextResponse> => {
  const response = await axios.post<GISContextResponse>(`${API_BASE_URL}/gis/context`, {
    latitude,
    longitude,
  });
  return response.data;
};

export const fetchGISManifest = async (): Promise<ManifestData> => {
  const response = await axios.get<ManifestData>(`${API_BASE_URL}/gis/manifest`);
  return response.data;
};

export const fetchGISLayer = async (layerName: string): Promise<any> => {
  const response = await axios.get(`${API_BASE_URL}/gis/layers/${layerName}`);
  return response.data;
};
