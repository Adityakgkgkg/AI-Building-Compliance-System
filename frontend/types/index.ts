/**
 * AI Building Compliance System — Shared TypeScript Interfaces
 *
 * These types define the contract between frontend and backend.
 * Placeholder interfaces are included for future sprint modules.
 */

// ── Upload ──────────────────────────────────────────────────────
export interface UploadResponse {
  filename: string;
  size: number;
  type: string;
  upload_time: string;
}

// ── Health ──────────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
}

// ── Building Information (Sprint 2+) ────────────────────────────
export interface BuildingInfo {
  id?: string;
  name?: string;
  description?: string;
  floors?: number;
  totalArea?: number;
  buildingType?: string;
  location?: GeoLocation;
  metadata?: Record<string, unknown>;
}

// ── Compliance (Sprint 3+) ──────────────────────────────────────
export interface ComplianceResult {
  id?: string;
  buildingId?: string;
  status?: "pass" | "fail" | "warning" | "pending";
  rules?: ComplianceRule[];
  score?: number;
  timestamp?: string;
}

export interface ComplianceRule {
  id?: string;
  name?: string;
  description?: string;
  category?: string;
  result?: "pass" | "fail" | "warning";
  details?: string;
}

// ── GIS Context (Sprint 4+) ────────────────────────────────────
export interface GISContext {
  id?: string;
  buildingId?: string;
  location?: GeoLocation;
  zoning?: string;
  surroundingBuildings?: SurroundingBuilding[];
  urbanDensity?: number;
  elevation?: number;
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  address?: string;
}

export interface SurroundingBuilding {
  id?: string;
  distance?: number;
  height?: number;
  type?: string;
}

// ── AI Recommendations (Sprint 5+) ─────────────────────────────
export interface AIRecommendation {
  id?: string;
  buildingId?: string;
  category?: string;
  severity?: "info" | "warning" | "critical";
  title?: string;
  description?: string;
  suggestedAction?: string;
  confidence?: number;
}

// ── IFC Parser — Module 1 ──────────────────────────────────────
export interface UploadIFCResponse {
  file_id: string;
  filename: string;
  status: string;
}

export interface ParserBuildingInfo {
  project_name: string | null;
  building_name: string | null;
  site_name: string | null;
  description: string | null;
  ifc_schema: string | null;
  storeys: number;
  units: string | null;
  owner: string | null;
}

export interface ParserElementCounts {
  walls: number;
  doors: number;
  windows: number;
  slabs: number;
  columns: number;
  beams: number;
  roofs: number;
  stairs: number;
  spaces: number;
  openings: number;
}

export interface ParserGeometry {
  gross_floor_area: number | null;
  height: number | null;
  storey_heights: number[] | null;
  footprint: number | null;
  bounding_box: {
    min_x: number; min_y: number; min_z: number;
    max_x: number; max_y: number; max_z: number;
  } | null;
}

export interface ParseResult {
  building: ParserBuildingInfo;
  elements: ParserElementCounts;
  geometry: ParserGeometry;
}

// ── API Error ───────────────────────────────────────────────────
export interface APIError {
  detail: string;
  error?: string;
}
