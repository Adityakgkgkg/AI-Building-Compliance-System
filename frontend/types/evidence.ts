/**
 * EvidenceBundle TypeScript types
 * ================================
 * Strict mirror of the backend Pydantic EvidenceBundle schema.
 * Every field maps 1-to-1 from the canonical Python model.
 * No optional widening — all required backend fields are required here too.
 */

// ── Dataset Provenance ────────────────────────────────────────────────────────
export interface DatasetProvenance {
  dataset_name: string;
  authority: string;
  source_url: string;
  license: string;
  feature_id: string | null;
  observation: string;
}

// ── Building Evidence (Module 1) ──────────────────────────────────────────────
export interface BuildingEvidence {
  building_id: string;
  building_name: string;
  ifc_file: string;
  building_type: string;
  plot_area: number;
  builtup_area: number;
  height: number;
  floors: number;
  fsi: number;
  ground_coverage: number;
  occupancy: string;
}

// ── Classification Evidence (Module 2) ────────────────────────────────────────
export interface ClassificationEvidence {
  predicted_type: string;
  confidence: number;
  reason: string;
}

// ── GIS Evidence (Module 3) ───────────────────────────────────────────────────
export interface GISEvidence {
  authority: string;
  ward: string;
  ward_number: number | null;
  zone: string;
  road_name: string;
  road_width: number;
  land_use: string;
  lake_distance: number;
  lake_buffer: boolean;
  airport_zone: boolean;
  airport_height_limit: number | null;
  flood_risk: string;
  heritage_zone: boolean;
  dataset_manifest: DatasetProvenance[];
}

// ── Rule Result ───────────────────────────────────────────────────────────────
export interface RuleResult {
  rule_id: string;
  rule_name: string;
  status: 'PASSED' | 'FAILED' | 'WARNING';
  severity: 'BLOCKING' | 'MAJOR' | 'MINOR' | 'INFO';
  expected: string;
  actual: string;
  difference: string;
  message: string;
  clause: string;
  reference: string;
  recommendation: string;
}

// ── Compliance Evidence (Module 2) ────────────────────────────────────────────
export interface ComplianceEvidence {
  rules_checked: number;
  passed: number;
  failed: number;
  warnings: number;
  blocking: number;
  score: number;
  rule_results: RuleResult[];
}

// ── Collection Metadata ───────────────────────────────────────────────────────
export interface CollectionMetadata {
  collected_at: string;
  building_collection_ms: number;
  classification_collection_ms: number;
  gis_collection_ms: number;
  compliance_collection_ms: number;
  total_collection_ms: number;
  ifc_parser_version: string;
  classification_version: string;
  gis_engine_version: string;
  compliance_engine_version: string;
}

// ── Root Evidence Bundle ──────────────────────────────────────────────────────
export interface EvidenceBundle {
  report_id: string;
  timestamp: string;
  building: BuildingEvidence;
  classification: ClassificationEvidence;
  gis: GISEvidence;
  compliance: ComplianceEvidence;
  metadata: CollectionMetadata;
  software_version: string;
}

// ── Module Error (HTTP 503 from backend) ─────────────────────────────────────
export interface ModuleErrorDetail {
  error_code: string;
  module: string;
  detail: string;
}

// ── Dashboard State ───────────────────────────────────────────────────────────
export type DashboardState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; bundle: EvidenceBundle }
  | { status: 'module_error'; error: ModuleErrorDetail; httpStatus: number }
  | { status: 'network_error'; message: string };

// ── Rule filter/sort state ────────────────────────────────────────────────────
export type RuleStatus = 'ALL' | 'PASSED' | 'FAILED' | 'WARNING';
export type RuleSeverity = 'ALL' | 'BLOCKING' | 'MAJOR' | 'MINOR' | 'INFO';
export type SortField = 'rule_id' | 'rule_name' | 'status' | 'severity';
export type SortDir = 'asc' | 'desc';
