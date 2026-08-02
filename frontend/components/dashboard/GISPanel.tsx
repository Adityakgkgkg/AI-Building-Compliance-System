'use client';

/**
 * GISPanel Component
 * ===================
 * Renders the urban spatial context from GISEvidence.
 * Displays ward, zone, road, lake, airport, flood risk, and dataset provenance.
 * All values are projected directly from EvidenceBundle.gis — no calculation.
 */

import type { GISEvidence, DatasetProvenance } from '@/types/evidence';

interface Props {
  gis: GISEvidence;
}

// ── Pill badges ───────────────────────────────────────────────────────────────

function RiskBadge({ risk }: { risk: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    Low:    { bg: 'rgba(16,185,129,0.12)',  text: '#10b981' },
    Medium: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
    High:   { bg: 'rgba(239,68,68,0.12)',  text: '#ef4444' },
  };
  const style = map[risk] ?? { bg: 'rgba(148,163,184,0.1)', text: '#94a3b8' };
  return (
    <span
      className="text-xs px-2.5 py-1 rounded-full font-semibold"
      style={{ background: style.bg, color: style.text }}
    >
      {risk}
    </span>
  );
}

function BoolBadge({ value, trueLabel, falseLabel }: { value: boolean; trueLabel: string; falseLabel: string }) {
  return (
    <span
      className="text-xs px-2.5 py-1 rounded-full font-semibold"
      style={
        value
          ? { background: 'rgba(239,68,68,0.12)', color: '#ef4444' }
          : { background: 'rgba(16,185,129,0.12)', color: '#10b981' }
      }
    >
      {value ? trueLabel : falseLabel}
    </span>
  );
}

// ── Single row ────────────────────────────────────────────────────────────────

function Row({ label, right }: { label: string; right: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2.5" style={{ borderBottom: '1px solid rgba(148,163,184,0.06)' }}>
      <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
        {label}
      </span>
      <span className="text-sm font-semibold text-right" style={{ color: 'var(--text-primary)', maxWidth: '60%' }}>
        {right}
      </span>
    </div>
  );
}

// ── Dataset provenance ────────────────────────────────────────────────────────

function DatasetRow({ ds }: { ds: DatasetProvenance }) {
  return (
    <div
      className="rounded-lg px-3 py-2.5"
      style={{ background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.1)' }}
    >
      <p className="text-xs font-semibold" style={{ color: '#06b6d4' }}>
        {ds.dataset_name}
      </p>
      <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
        {ds.authority} · {ds.license}
      </p>
      <p className="text-xs mt-0.5 line-clamp-1" style={{ color: 'var(--text-muted)', opacity: 0.7 }}>
        {ds.observation}
      </p>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function GISPanel({ gis }: Props) {
  return (
    <div
      className="rounded-xl overflow-hidden animate-fade-in-up opacity-0"
      style={{
        background: 'rgba(17,24,39,0.8)',
        border: '1px solid rgba(6,182,212,0.15)',
        animationDelay: '250ms',
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
          style={{ background: 'rgba(6,182,212,0.15)', color: '#06b6d4' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="12" r="10" />
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
        </div>
        <div>
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            GIS Urban Context
          </h2>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {gis.authority} · {gis.zone}
          </p>
        </div>
      </div>

      {/* Spatial data */}
      <div className="px-6 pt-4 pb-2">
        <Row label="Ward" right={`${gis.ward}${gis.ward_number != null ? ` (No. ${gis.ward_number})` : ''}`} />
        <Row label="Zone" right={gis.zone} />
        <Row label="Land Use" right={gis.land_use} />
        <Row label="Nearest Road" right={`${gis.road_name} · ${gis.road_width} m wide`} />
        <Row label="Lake Distance" right={`${gis.lake_distance.toFixed(0)} m`} />
        <Row label="Lake Buffer" right={<BoolBadge value={gis.lake_buffer} trueLabel="⚠ In Buffer" falseLabel="✓ Clear" />} />
        <Row label="Airport Zone" right={
          gis.airport_zone
            ? <span style={{ color: '#ef4444' }} className="text-sm font-semibold">
                Restricted {gis.airport_height_limit != null ? `(≤ ${gis.airport_height_limit} m)` : ''}
              </span>
            : <span style={{ color: '#10b981' }} className="text-sm font-semibold">Clear</span>
        } />
        <Row label="Flood Risk" right={<RiskBadge risk={gis.flood_risk} />} />
        <Row label="Heritage Zone" right={<BoolBadge value={gis.heritage_zone} trueLabel="Protected" falseLabel="No" />} />
      </div>

      {/* Dataset Provenance */}
      {gis.dataset_manifest.length > 0 && (
        <div className="px-6 pb-5">
          <p
            className="text-xs font-semibold uppercase tracking-wider mb-2 pt-3"
            style={{ color: 'var(--text-muted)', borderTop: '1px solid rgba(148,163,184,0.08)' }}
          >
            Dataset Provenance ({gis.dataset_manifest.length})
          </p>
          <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
            {gis.dataset_manifest.map((ds, i) => (
              <DatasetRow key={i} ds={ds} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
