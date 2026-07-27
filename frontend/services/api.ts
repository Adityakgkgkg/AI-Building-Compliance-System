/**
 * AI Building Compliance System — API Service
 *
 * Centralized Axios instance and API functions.
 * All backend communication goes through this module.
 */

import axios, { AxiosError } from "axios";
import type { UploadResponse, HealthResponse, APIError, UploadIFCResponse, ParseResult } from "@/types";

// ── Axios Instance ──────────────────────────────────────────────
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: {
    Accept: "application/json",
  },
});

// ── Response Interceptor (Global Error Handler) ─────────────────
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<APIError>) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      "An unexpected error occurred";

    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${message}`);

    return Promise.reject(error);
  }
);

// ── API Functions ───────────────────────────────────────────────

/**
 * Check the health status of the backend API.
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
}

/**
 * Upload a building plan file (IFC or DXF).
 *
 * @param file - The file to upload
 * @param onProgress - Optional callback for upload progress (0-100)
 */
export async function uploadFile(
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<UploadResponse>("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percent);
      }
    },
  });

  return response.data;
}

// ── Module 1: IFC Parser API ─────────────────────────────────

/**
 * Upload an IFC file to the parser endpoint.
 * Returns a file_id UUID for subsequent parse calls.
 */
export async function uploadIFC(
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadIFCResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<UploadIFCResponse>("/parser/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (evt.total && onProgress) {
        onProgress(Math.round((evt.loaded * 100) / evt.total));
      }
    },
  });
  return response.data;
}

/**
 * Parse a previously uploaded IFC file.
 * Returns the full ParseResult JSON contract.
 */
export async function parseIFC(fileId: string): Promise<ParseResult> {
  const response = await api.post<ParseResult>(`/parser/parse/${fileId}`);
  return response.data;
}

// ── Future API Functions (Sprint 2+) ────────────────────────────
// export async function getBuildingInfo(id: string): Promise<BuildingInfo> { ... }
// export async function checkCompliance(id: string): Promise<ComplianceResult> { ... }
// export async function getGISContext(id: string): Promise<GISContext> { ... }
// export async function getRecommendations(id: string): Promise<AIRecommendation[]> { ... }

export default api;
