'use client';

/**
 * ComplianceSummary Component
 * ============================
 * Visual summary bar showing passed/failed/warning/blocking rule counts.
 * Score progress bar and breakdown pill row.
 * Reads directly from EvidenceBundle.compliance — no recalculation.
 */

import type { ComplianceEvidence } from '@/types/evidence';

interface Props {
  compliance: ComplianceEvidence;
}

function scoreColor(score: number) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#f59e0b';
  return '#ef4444';
}

interface StatPillProps {
  label: string;
  count: number;
  color: string;
  bg: string;
}

function StatPill({ label, count, color, bg }: StatPillProps) {
  return (
    <div
      className="flex flex-col items-center justify-center px-4 py-3 rounded-xl flex-1 min-w-0"
      style={{ background: bg, border: `1px solid ${color}28` }}
    >
      <span className="text-xl font-bold" style={{ color }}>
        {count}
      </span>
      <span className="text-xs font-medium mt-0.5 text-center" style={{ color }}>
        {label}
      </span>
    </div>
  );
}

export default function ComplianceSummary({ compliance }: Props) {
  const color = scoreColor(compliance.score);
  const { rules_checked, passed, failed, warnings, blocking, score } = compliance;

  // Proportional widths for the stacked progress bar
  const totalSafe = rules_checked > 0 ? rules_checked : 1;
  const passedPct = (passed / totalSafe) * 100;
  const failedPct = (failed / totalSafe) * 100;
  const warningPct = (warnings / totalSafe) * 100;

  return (
    <div
      className="rounded-xl overflow-hidden animate-fade-in-up opacity-0"
      style={{
        background: 'rgba(17,24,39,0.8)',
        border: '1px solid rgba(148,163,184,0.1)',
        animationDelay: '350ms',
        animationFillMode: 'forwards',
      }}
    >
      {/* Header */}
      <div
        className="px-6 py-4 flex items-center justify-between"
        style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: `${color}18`, color }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            Compliance Summary
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold" style={{ color }}>
            {score.toFixed(1)}%
          </span>
          {blocking > 0 && (
            <span
              className="text-xs px-2 py-0.5 rounded-full font-bold"
              style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}
            >
              {blocking} BLOCKING
            </span>
          )}
        </div>
      </div>

      <div className="p-6 space-y-5">
        {/* Stacked progress bar */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Rule Evaluation Breakdown
            </span>
            <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
              {rules_checked} total
            </span>
          </div>
          <div className="flex rounded-full overflow-hidden h-3" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <div style={{ width: `${passedPct}%`, background: '#10b981' }} title={`Passed: ${passed}`} />
            <div style={{ width: `${warningPct}%`, background: '#f59e0b' }} title={`Warnings: ${warnings}`} />
            <div style={{ width: `${failedPct}%`, background: '#ef4444' }} title={`Failed: ${failed}`} />
          </div>
          <div className="flex gap-4 mt-2">
            {[
              { label: 'Passed', color: '#10b981' },
              { label: 'Warnings', color: '#f59e0b' },
              { label: 'Failed', color: '#ef4444' },
            ].map(({ label, color: c }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ background: c }} />
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Stat pills */}
        <div className="flex gap-3">
          <StatPill label="Passed" count={passed} color="#10b981" bg="rgba(16,185,129,0.08)" />
          <StatPill label="Failed" count={failed} color="#ef4444" bg="rgba(239,68,68,0.08)" />
          <StatPill label="Warnings" count={warnings} color="#f59e0b" bg="rgba(245,158,11,0.08)" />
          <StatPill label="Blocking" count={blocking} color={blocking > 0 ? '#ef4444' : '#94a3b8'} bg={blocking > 0 ? 'rgba(239,68,68,0.08)' : 'rgba(148,163,184,0.06)'} />
        </div>
      </div>
    </div>
  );
}
