'use client';

/**
 * RuleTable Component
 * ====================
 * Full-featured rule evaluation table with:
 * - Text search across rule_id, rule_name, clause, message
 * - Status filter (ALL / PASSED / FAILED / WARNING)
 * - Severity filter (ALL / BLOCKING / MAJOR / MINOR / INFO)
 * - Column sorting (rule_id, rule_name, status, severity)
 * - Expandable row → EvidenceDetailsPanel for each rule
 * - Row count badge and clear-filters button
 *
 * All data sourced from EvidenceBundle.compliance.rule_results.
 */

import { useState, useMemo, useCallback } from 'react';
import type { RuleResult } from '@/types/evidence';
import type { RuleStatus, RuleSeverity, SortField, SortDir } from '@/types/evidence';
import EvidenceDetailsPanel from './EvidenceDetailsPanel';

interface Props {
  rules: RuleResult[];
}

// ── Badge helpers ─────────────────────────────────────────────────────────────

const STATUS_STYLE: Record<string, { bg: string; text: string; dot: string }> = {
  PASSED:  { bg: 'rgba(16,185,129,0.12)',  text: '#10b981', dot: '#10b981' },
  FAILED:  { bg: 'rgba(239,68,68,0.12)',   text: '#ef4444', dot: '#ef4444' },
  WARNING: { bg: 'rgba(245,158,11,0.12)',  text: '#f59e0b', dot: '#f59e0b' },
};

const SEVERITY_STYLE: Record<string, { bg: string; text: string }> = {
  BLOCKING: { bg: 'rgba(239,68,68,0.18)',   text: '#ef4444' },
  MAJOR:    { bg: 'rgba(249,115,22,0.12)',  text: '#f97316' },
  MINOR:    { bg: 'rgba(245,158,11,0.12)',  text: '#f59e0b' },
  INFO:     { bg: 'rgba(148,163,184,0.1)',  text: '#94a3b8' },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLE[status] ?? { bg: 'rgba(148,163,184,0.1)', text: '#94a3b8', dot: '#94a3b8' };
  return (
    <span
      className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-semibold whitespace-nowrap"
      style={{ background: s.bg, color: s.text }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.dot }} />
      {status}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const s = SEVERITY_STYLE[severity] ?? { bg: 'rgba(148,163,184,0.1)', text: '#94a3b8' };
  return (
    <span
      className="inline-flex text-xs px-2.5 py-1 rounded-full font-semibold whitespace-nowrap"
      style={{ background: s.bg, color: s.text }}
    >
      {severity}
    </span>
  );
}

// ── Sort icon ─────────────────────────────────────────────────────────────────

function SortIcon({ field, active, dir }: { field: SortField; active: SortField; dir: SortDir }) {
  const isActive = field === active;
  return (
    <span className="ml-1 inline-flex flex-col" style={{ opacity: isActive ? 1 : 0.3 }}>
      <svg width="8" height="5" viewBox="0 0 8 5" fill={isActive && dir === 'asc' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.5">
        <path d="M1 4L4 1L7 4" />
      </svg>
      <svg width="8" height="5" viewBox="0 0 8 5" fill={isActive && dir === 'desc' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.5">
        <path d="M1 1L4 4L7 1" />
      </svg>
    </span>
  );
}

// ── Filter pill ───────────────────────────────────────────────────────────────

function FilterPill<T extends string>({
  value, active, onChange, label,
}: {
  value: T; active: T; onChange: (v: T) => void; label: string;
}) {
  const isActive = value === active;
  return (
    <button
      onClick={() => onChange(value)}
      className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150"
      style={{
        background: isActive ? 'rgba(139,92,246,0.18)' : 'rgba(255,255,255,0.04)',
        color: isActive ? '#8b5cf6' : 'var(--text-muted)',
        border: isActive ? '1px solid rgba(139,92,246,0.35)' : '1px solid rgba(148,163,184,0.1)',
      }}
    >
      {label}
    </button>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

const SEVERITY_ORDER: Record<string, number> = { BLOCKING: 0, MAJOR: 1, MINOR: 2, INFO: 3 };
const STATUS_ORDER: Record<string, number>   = { FAILED: 0, WARNING: 1, PASSED: 2 };

export default function RuleTable({ rules }: Props) {
  const [search, setSearch]         = useState('');
  const [statusFilter, setStatus]   = useState<RuleStatus>('ALL');
  const [severityFilter, setSev]    = useState<RuleSeverity>('ALL');
  const [sortField, setSortField]   = useState<SortField>('severity');
  const [sortDir, setSortDir]       = useState<SortDir>('asc');
  const [expanded, setExpanded]     = useState<string | null>(null);

  const handleSort = useCallback((field: SortField) => {
    setSortField(prev => {
      setSortDir(d => prev === field ? (d === 'asc' ? 'desc' : 'asc') : 'asc');
      return field;
    });
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return rules
      .filter(r =>
        (statusFilter === 'ALL' || r.status === statusFilter) &&
        (severityFilter === 'ALL' || r.severity === severityFilter) &&
        (!q || [r.rule_id, r.rule_name, r.clause, r.message].some(s => s.toLowerCase().includes(q)))
      )
      .sort((a, b) => {
        let cmp = 0;
        if (sortField === 'status')   cmp = (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9);
        else if (sortField === 'severity') cmp = (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9);
        else cmp = (a[sortField] ?? '').localeCompare(b[sortField] ?? '');
        return sortDir === 'asc' ? cmp : -cmp;
      });
  }, [rules, search, statusFilter, severityFilter, sortField, sortDir]);

  const hasFilters = search || statusFilter !== 'ALL' || severityFilter !== 'ALL';

  return (
    <div
      className="rounded-xl overflow-hidden animate-fade-in-up opacity-0"
      style={{
        background: 'rgba(17,24,39,0.8)',
        border: '1px solid rgba(148,163,184,0.1)',
        animationDelay: '450ms',
        animationFillMode: 'forwards',
      }}
    >
      {/* ── Toolbar ──────────────────────────────────────────────────────── */}
      <div
        className="px-5 py-4 space-y-3"
        style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}
      >
        {/* Title row */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(139,92,246,0.15)', color: '#8b5cf6' }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
                <rect x="9" y="3" width="6" height="4" rx="1" />
                <path d="M9 12h6M9 16h4" />
              </svg>
            </div>
            <h2 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
              Rule Evaluation
            </h2>
            <span
              className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ background: 'rgba(139,92,246,0.12)', color: '#8b5cf6' }}
            >
              {filtered.length} / {rules.length}
            </span>
          </div>

          {hasFilters && (
            <button
              onClick={() => { setSearch(''); setStatus('ALL'); setSev('ALL'); }}
              className="text-xs px-3 py-1 rounded-lg transition-all duration-150"
              style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Search + filters */}
        <div className="flex flex-wrap gap-2 items-center">
          {/* Search */}
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2"
              width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="Search rules…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg text-xs outline-none transition-all duration-150"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(148,163,184,0.15)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          {/* Status filters */}
          <div className="flex gap-1.5 flex-wrap">
            {(['ALL', 'PASSED', 'FAILED', 'WARNING'] as RuleStatus[]).map(s => (
              <FilterPill key={s} value={s} active={statusFilter} onChange={setStatus} label={s === 'ALL' ? 'All Status' : s} />
            ))}
          </div>

          {/* Severity filters */}
          <div className="flex gap-1.5 flex-wrap">
            {(['ALL', 'BLOCKING', 'MAJOR', 'MINOR', 'INFO'] as RuleSeverity[]).map(s => (
              <FilterPill key={s} value={s} active={severityFilter} onChange={setSev} label={s === 'ALL' ? 'All Severity' : s} />
            ))}
          </div>
        </div>
      </div>

      {/* ── Table ─────────────────────────────────────────────────────────── */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}>
              {([
                { key: 'rule_id',   label: 'Rule ID'   },
                { key: 'rule_name', label: 'Name'      },
                { key: 'status',    label: 'Status'    },
                { key: 'severity',  label: 'Severity'  },
              ] as { key: SortField; label: string }[]).map(col => (
                <th
                  key={col.key}
                  className="text-left px-5 py-3 cursor-pointer select-none"
                  style={{ color: 'var(--text-muted)' }}
                  onClick={() => handleSort(col.key)}
                >
                  <span className="text-xs font-semibold uppercase tracking-wider">
                    {col.label}
                    <SortIcon field={col.key} active={sortField} dir={sortDir} />
                  </span>
                </th>
              ))}
              <th className="text-left px-5 py-3">
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  Clause
                </span>
              </th>
              <th className="px-5 py-3 w-10" />
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center">
                  <p style={{ color: 'var(--text-muted)' }} className="text-sm">
                    No rules match the current filters.
                  </p>
                </td>
              </tr>
            ) : (
              filtered.map(rule => {
                const isExpanded = expanded === rule.rule_id;
                return (
                  <>
                    <tr
                      key={rule.rule_id}
                      onClick={() => setExpanded(isExpanded ? null : rule.rule_id)}
                      className="cursor-pointer transition-all duration-150"
                      style={{
                        borderBottom: '1px solid rgba(148,163,184,0.05)',
                        background: isExpanded
                          ? 'rgba(139,92,246,0.06)'
                          : undefined,
                      }}
                      onMouseEnter={e => { if (!isExpanded) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.02)'; }}
                      onMouseLeave={e => { if (!isExpanded) (e.currentTarget as HTMLElement).style.background = ''; }}
                    >
                      <td className="px-5 py-3.5">
                        <span className="text-xs font-mono" style={{ color: 'var(--accent-cyan)' }}>
                          {rule.rule_id}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 max-w-[220px]">
                        <span className="text-sm font-medium line-clamp-1" style={{ color: 'var(--text-primary)' }}>
                          {rule.rule_name}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <StatusBadge status={rule.status} />
                      </td>
                      <td className="px-5 py-3.5">
                        <SeverityBadge severity={rule.severity} />
                      </td>
                      <td className="px-5 py-3.5 max-w-[200px]">
                        <span className="text-xs line-clamp-1" style={{ color: 'var(--text-muted)' }}>
                          {rule.clause}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <span
                          className="transition-transform duration-200 inline-block"
                          style={{
                            color: 'var(--text-muted)',
                            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                          }}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M6 9l6 6 6-6" />
                          </svg>
                        </span>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${rule.rule_id}-detail`}>
                        <td
                          colSpan={6}
                          style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}
                        >
                          <EvidenceDetailsPanel rule={rule} />
                        </td>
                      </tr>
                    )}
                  </>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
