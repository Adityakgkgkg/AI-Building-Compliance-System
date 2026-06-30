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

// ── API Error ───────────────────────────────────────────────────
export interface APIError {
  detail: string;
  error?: string;
}
