'use client';

/**
 * EvidenceDetailsPanel Component
 * ===============================
 * Expanded detail view for a specific RuleResult.
 * Displays the message, expected vs actual values, clause info, and recommendation.
 * Shows nested cleanly within the RuleTable row.
 */

import type { RuleResult } from '@/types/evidence';

interface Props {
  rule: RuleResult;
}

function DetailBlock({ label, value, bg = 'rgba(255,255,255,0.03)' }: { label: string; value: string; bg?: string }) {
  return (
    <div className="rounded-lg p-3" style={{ background: bg, border: '1px solid rgba(148,163,184,0.08)' }}>
      <p className="text-xs font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>
        {label}
      </p>
      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
        {value}
      </p>
    </div>
  );
}

export default function EvidenceDetailsPanel({ rule }: Props) {
  // Determine if it's a failure to highlight difference in red
  const isFailed = rule.status === 'FAILED' || rule.severity === 'BLOCKING';

  return (
    <div className="p-5 animate-fade-in" style={{ background: 'rgba(139,92,246,0.02)' }}>
      <div className="flex items-start gap-4 mb-5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
          style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
            Evaluation Message
          </h3>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            {rule.message}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
        <DetailBlock label="Expected" value={rule.expected} />
        <DetailBlock label="Actual Found" value={rule.actual} />
        <DetailBlock
          label="Difference"
          value={rule.difference}
          bg={isFailed ? 'rgba(239,68,68,0.06)' : 'rgba(255,255,255,0.03)'}
        />
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <DetailBlock label="Regulatory Clause & Reference" value={`${rule.clause} — ${rule.reference}`} />
        </div>
        <div className="flex-1">
          <DetailBlock
            label="Recommendation / Action Required"
            value={rule.recommendation}
            bg={isFailed ? 'rgba(249,115,22,0.06)' : 'rgba(16,185,129,0.06)'}
          />
        </div>
      </div>
    </div>
  );
}
