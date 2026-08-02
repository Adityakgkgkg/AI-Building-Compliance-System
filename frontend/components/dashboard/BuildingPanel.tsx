'use client';

/**
 * BuildingPanel Component
 * ========================
 * Displays IFC-parsed building metadata and classification confidence.
 * Two-column grid of label/value pairs.
 * All values sourced directly from EvidenceBundle.building + .classification.
 */

import type { BuildingEvidence, ClassificationEvidence } from '@/types/evidence';

interface Props {
  building: BuildingEvidence;
  classification: ClassificationEvidence;
}

function Field({ label, value, accent = false }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
        {label}
      </span>
      <span
        className="text-sm font-semibold"
        style={{ color: accent ? 'var(--accent-cyan)' : 'var(--text-primary)' }}
      >
        {value}
      </span>
    </div>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 85 ? '#10b981' : pct >= 65 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-3">
      <div
        className="flex-1 rounded-full overflow-hidden"
        style={{ height: '6px', background: 'rgba(255,255,255,0.06)' }}
      >
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 6px ${color}88` }}
        />
      </div>
      <span className="text-sm font-bold w-10 text-right" style={{ color }}>
        {pct}%
      </span>
    </div>
  );
}

export default function BuildingPanel({ building, classification }: Props) {
  return (
    <div
      className="rounded-xl overflow-hidden animate-fade-in-up opacity-0"
      style={{
        background: 'rgba(17,24,39,0.8)',
        border: '1px solid rgba(139,92,246,0.15)',
        animationDelay: '150ms',
        animationFillMode: 'forwards',
      }}
    >
      {/* Header */}
      <div
        className="px-6 py-4 flex items-center gap-3"
        style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(139,92,246,0.15)', color: '#8b5cf6' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4" />
            <path d="M9 9v.01M9 12v.01M9 15v.01M9 18v.01" />
          </svg>
        </div>
        <div>
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            Building Summary
          </h2>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {building.ifc_file}
          </p>
        </div>
      </div>

      {/* Body */}
      <div className="p-6 space-y-6">
        {/* Building metadata grid */}
        <div className="grid grid-cols-2 gap-x-6 gap-y-4">
          <Field label="Building ID" value={building.building_id} />
          <Field label="Building Name" value={building.building_name} />
          <Field label="Building Type" value={building.building_type} />
          <Field label="Occupancy" value={building.occupancy} />
          <Field label="Plot Area" value={`${building.plot_area.toLocaleString()} m²`} />
          <Field label="Built-up Area" value={`${building.builtup_area.toLocaleString()} m²`} />
          <Field label="Height" value={`${building.height} m`} />
          <Field label="Floors" value={building.floors} />
          <Field label="FSI" value={building.fsi.toFixed(2)} accent />
          <Field label="Ground Coverage" value={`${building.ground_coverage.toFixed(1)}%`} accent />
        </div>

        {/* Divider */}
        <div style={{ borderTop: '1px solid rgba(148,163,184,0.08)' }} />

        {/* Classification */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--text-muted)' }}>
            AI Classification
          </p>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
              {classification.predicted_type}
            </span>
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: 'rgba(139,92,246,0.12)', color: '#8b5cf6' }}
            >
              {classification.predicted_type}
            </span>
          </div>
          <ConfidenceBar value={classification.confidence} />
          <p className="text-xs mt-2 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
            {classification.reason}
          </p>
        </div>
      </div>
    </div>
  );
}
