'use client';

/**
 * Dashboard Page (Sprint 2)
 * ==========================
 * Main entry point for the Municipal Compliance Dashboard.
 * Fetches the EvidenceBundle from the backend and coordinates all panels.
 * Provides robust loading skeletons and structured error states.
 */

import { useState, useEffect } from 'react';
import type { DashboardState } from '@/types/evidence';
import { fetchReportContext } from '@/services/reportService';
import OverviewCards from '@/components/dashboard/OverviewCards';
import BuildingPanel from '@/components/dashboard/BuildingPanel';
import GISPanel from '@/components/dashboard/GISPanel';
import ComplianceSummary from '@/components/dashboard/ComplianceSummary';
import RuleTable from '@/components/dashboard/RuleTable';
import { DashboardSkeleton } from '@/components/dashboard/Skeletons';

// For the demo, we assume the user uploaded this file and it's stored in session/context.
// In a real flow, this would come from the Upload page redirect.
const MOCK_IFC_FILE = 'plan.ifc';
const MOCK_LAT = 12.9250;
const MOCK_LON = 77.5938;

export default function DashboardPage() {
  const [state, setState] = useState<DashboardState>({ status: 'idle' });

  useEffect(() => {
    let mounted = true;

    async function loadData() {
      setState({ status: 'loading' });
      const result = await fetchReportContext(MOCK_IFC_FILE, MOCK_LAT, MOCK_LON);
      
      if (!mounted) return;

      if (result.ok) {
        setState({ status: 'success', bundle: result.bundle });
      } else if ('moduleError' in result) {
        setState({ status: 'module_error', error: result.moduleError, httpStatus: result.httpStatus });
      } else {
        setState({ status: 'network_error', message: result.networkError });
      }
    }

    loadData();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="page-container pb-20">
      <div className="section-container">
        {/* ── Header ───────────────────────────────────────── */}
        <div className="mb-10 pt-8">
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold tracking-wider uppercase mb-6 animate-fade-in"
            style={{
              background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.2)',
              color: 'var(--accent-cyan)',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            Sprint 2 Dashboard
          </div>

          <h1 className="text-3xl sm:text-4xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
            Compliance <span className="gradient-text">Decision Engine</span>
          </h1>
          <p className="text-base max-w-2xl" style={{ color: 'var(--text-muted)' }}>
            Single source of truth for municipal building compliance. All data is canonical and sourced from the unified Evidence Collection Layer.
          </p>
        </div>

        {/* ── Content Area ─────────────────────────────────── */}
        <div className="min-h-[50vh]">
          {state.status === 'idle' || state.status === 'loading' ? (
            <DashboardSkeleton />
          ) : state.status === 'success' ? (
            <div className="space-y-6 animate-fade-in">
              <OverviewCards bundle={state.bundle} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-6">
                  <BuildingPanel building={state.bundle.building} classification={state.bundle.classification} />
                  <ComplianceSummary compliance={state.bundle.compliance} />
                </div>
                <GISPanel gis={state.bundle.gis} />
              </div>
              <RuleTable rules={state.bundle.compliance.rule_results} />
            </div>
          ) : state.status === 'module_error' ? (
            <div
              className="rounded-xl p-8 animate-fade-in"
              style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)' }}
            >
              <div className="flex items-center gap-4 mb-4">
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center"
                  style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-red-500">Service Unavailable (HTTP {state.httpStatus})</h2>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Module: <code className="font-mono text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded">{state.error.module}</code>
                  </p>
                </div>
              </div>
              <p className="text-base mb-6" style={{ color: 'var(--text-primary)' }}>
                {state.error.detail}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="btn-primary bg-red-600 hover:bg-red-700"
                style={{ background: '#ef4444' }}
              >
                Retry Connection
              </button>
            </div>
          ) : (
            <div
              className="rounded-xl p-8 animate-fade-in"
              style={{ background: 'rgba(245,158,11,0.05)', border: '1px solid rgba(245,158,11,0.2)' }}
            >
              <h2 className="text-xl font-bold text-amber-500 mb-2">Network Error</h2>
              <p className="text-base mb-6" style={{ color: 'var(--text-primary)' }}>
                {state.message}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="btn-primary"
                style={{ background: '#f59e0b' }}
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
