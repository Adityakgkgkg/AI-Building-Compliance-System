'use client';

/**
 * OverviewCards Component
 * ========================
 * Four KPI cards at the top of the dashboard:
 * - Compliance Score (donut-style gauge)
 * - Rules Checked
 * - Blocking Violations
 * - GIS Ward
 *
 * All values read directly from EvidenceBundle — no calculation.
 */

import type { EvidenceBundle } from '@/types/evidence';

interface Props {
  bundle: EvidenceBundle;
}

function scoreColor(score: number): string {
  if (score >= 80) return '#10b981'; // emerald
  if (score >= 60) return '#f59e0b'; // amber
  return '#ef4444'; // red
}

function ScoreRing({ score }: { score: number }) {
  const color = scoreColor(score);
  const r = 28;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;

  return (
    <svg width="72" height="72" className="shrink-0">
      {/* Track */}
      <circle
        cx="36" cy="36" r={r}
        fill="none"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="6"
      />
      {/* Progress */}
      <circle
        cx="36" cy="36" r={r}
        fill="none"
        stroke={color}
        strokeWidth="6"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${circ}`}
        strokeDashoffset={circ * 0.25}
        style={{ filter: `drop-shadow(0 0 6px ${color}99)` }}
      />
      <text
        x="36" y="41"
        textAnchor="middle"
        fill={color}
        fontSize="13"
        fontWeight="700"
        fontFamily="system-ui"
      >
        {score.toFixed(0)}
      </text>
    </svg>
  );
}

interface KpiCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent: string;
  icon: React.ReactNode;
  delay?: number;
  right?: React.ReactNode;
}

function KpiCard({ label, value, sub, accent, icon, delay = 0, right }: KpiCardProps) {
  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-3 animate-fade-in-up opacity-0"
      style={{
        background: 'rgba(17,24,39,0.8)',
        border: `1px solid ${accent}28`,
        boxShadow: `0 0 20px ${accent}0d`,
        animationDelay: `${delay}ms`,
        animationFillMode: 'forwards',
      }}
    >
      <div className="flex items-start justify-between">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: `${accent}18`, color: accent }}
        >
          {icon}
        </div>
        {right}
      </div>
      <div>
        <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
          {value}
        </p>
        <p className="text-xs font-medium mt-0.5" style={{ color: accent }}>
          {label}
        </p>
        {sub && (
          <p className="text-xs mt-1 truncate" style={{ color: 'var(--text-muted)' }}>
            {sub}
          </p>
        )}
      </div>
    </div>
  );
}

export default function OverviewCards({ bundle }: Props) {
  const { compliance, gis, building } = bundle;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1 — Compliance Score */}
      <div
        className="col-span-2 lg:col-span-1 rounded-xl p-5 flex items-center gap-4 animate-fade-in-up opacity-0"
        style={{
          background: 'rgba(17,24,39,0.8)',
          border: `1px solid ${scoreColor(compliance.score)}28`,
          boxShadow: `0 0 20px ${scoreColor(compliance.score)}0d`,
          animationDelay: '0ms',
          animationFillMode: 'forwards',
        }}
      >
        <ScoreRing score={compliance.score} />
        <div>
          <p
            className="text-2xl font-bold"
            style={{ color: scoreColor(compliance.score) }}
          >
            {compliance.score.toFixed(1)}%
          </p>
          <p className="text-xs font-medium" style={{ color: scoreColor(compliance.score) }}>
            Compliance Score
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
            {compliance.rules_checked} rules evaluated
          </p>
        </div>
      </div>

      {/* 2 — Rules Checked */}
      <KpiCard
        label="Rules Checked"
        value={compliance.rules_checked}
        sub={`${compliance.passed} passed · ${compliance.failed} failed`}
        accent="#8b5cf6"
        delay={100}
        icon={
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
        }
      />

      {/* 3 — Blocking Violations */}
      <KpiCard
        label="Blocking Violations"
        value={compliance.blocking}
        sub={compliance.blocking === 0 ? 'Approval unblocked' : 'Approval blocked'}
        accent={compliance.blocking === 0 ? '#10b981' : '#ef4444'}
        delay={200}
        icon={
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" /><line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
          </svg>
        }
      />

      {/* 4 — GIS Ward */}
      <KpiCard
        label="BBMP Ward"
        value={gis.ward}
        sub={`${gis.zone} · ${gis.authority}`}
        accent="#06b6d4"
        delay={300}
        icon={
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
        }
      />
    </div>
  );
}
