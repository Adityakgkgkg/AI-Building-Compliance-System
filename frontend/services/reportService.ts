/**
 * Report Evidence API Service
 * ============================
 * Client for GET /api/v1/report/context.
 * Returns either an EvidenceBundle (HTTP 200) or a ModuleErrorDetail (HTTP 503).
 * All network errors are surfaced as typed results — never raw throws.
 */

import axios, { AxiosError } from 'axios';
import type { EvidenceBundle, ModuleErrorDetail } from '@/types/evidence';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export type ReportContextResult =
  | { ok: true; bundle: EvidenceBundle }
  | { ok: false; moduleError: ModuleErrorDetail; httpStatus: number }
  | { ok: false; networkError: string };

/**
 * Fetch the canonical EvidenceBundle from the backend.
 *
 * @param ifcFile  Filename of the uploaded IFC file.
 * @param lat      WGS84 latitude of the building site.
 * @param lon      WGS84 longitude of the building site.
 */
export async function fetchReportContext(
  ifcFile: string,
  lat: number,
  lon: number,
): Promise<ReportContextResult> {
  try {
    const response = await axios.get<EvidenceBundle>(
      `${API_BASE}/report/context`,
      {
        params: { ifc_file: ifcFile, lat, lon },
        timeout: 30_000,
      },
    );
    return { ok: true, bundle: response.data };
  } catch (err) {
    const axiosErr = err as AxiosError<ModuleErrorDetail>;

    if (axiosErr.response) {
      const httpStatus = axiosErr.response.status;
      const body = axiosErr.response.data;

      // Backend returns ModuleErrorDetail on 503
      if (httpStatus >= 400 && body && 'error_code' in body) {
        return { ok: false, moduleError: body, httpStatus };
      }

      return {
        ok: false,
        moduleError: {
          error_code: 'HTTP_ERROR',
          module: 'backend',
          detail: `Backend returned HTTP ${httpStatus}.`,
        },
        httpStatus,
      };
    }

    const networkError = axiosErr.message ?? 'Unable to reach the backend API.';
    return { ok: false, networkError };
  }
}
