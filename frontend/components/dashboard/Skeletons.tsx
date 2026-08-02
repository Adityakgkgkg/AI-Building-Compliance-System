'use client';

/**
 * Skeleton Components
 * ====================
 * Animated loading placeholders matching the exact layout of each dashboard panel.
 * Used while the EvidenceBundle is being fetched.
 */

function SkeletonBox({
  className = '',
  style,
}: {
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={`rounded-lg animate-shimmer ${className}`}
      style={{
        background:
          'linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(139,92,246,0.07) 50%, rgba(255,255,255,0.04) 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.8s ease-in-out infinite',
        ...style,
      }}
    />
  );
}

/** Skeleton for the 4 KPI overview cards */
export function OverviewCardsSkeleton() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl p-5"
          style={{
            background: 'rgba(17,24,39,0.7)',
            border: '1px solid rgba(148,163,184,0.1)',
          }}
        >
          <SkeletonBox className="h-3 w-20 mb-3" />
          <SkeletonBox className="h-8 w-16 mb-2" />
          <SkeletonBox className="h-3 w-24" />
        </div>
      ))}
    </div>
  );
}

/** Skeleton for Building Summary + Classification panels */
export function BuildingSummarySkeleton() {
  return (
    <div
      className="rounded-xl p-6"
      style={{
        background: 'rgba(17,24,39,0.7)',
        border: '1px solid rgba(148,163,184,0.1)',
      }}
    >
      <SkeletonBox className="h-4 w-40 mb-6" />
      <div className="grid grid-cols-2 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i}>
            <SkeletonBox className="h-3 w-24 mb-2" />
            <SkeletonBox className="h-5 w-32" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Skeleton for GIS Context panel */
export function GISPanelSkeleton() {
  return (
    <div
      className="rounded-xl p-6"
      style={{
        background: 'rgba(17,24,39,0.7)',
        border: '1px solid rgba(148,163,184,0.1)',
      }}
    >
      <SkeletonBox className="h-4 w-36 mb-6" />
      <div className="space-y-4">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between">
            <SkeletonBox className="h-3 w-32" />
            <SkeletonBox className="h-5 w-24" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Skeleton for the Rule Evaluation table */
export function RuleTableSkeleton() {
  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        background: 'rgba(17,24,39,0.7)',
        border: '1px solid rgba(148,163,184,0.1)',
      }}
    >
      {/* Table header */}
      <div
        className="grid grid-cols-5 gap-4 px-5 py-3"
        style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}
      >
        {['Rule ID', 'Name', 'Status', 'Severity', 'Clause'].map((_, i) => (
          <SkeletonBox key={i} className="h-3 w-full" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="grid grid-cols-5 gap-4 px-5 py-4"
          style={{ borderBottom: '1px solid rgba(148,163,184,0.05)' }}
        >
          <SkeletonBox className="h-4 w-full" />
          <SkeletonBox className="h-4 w-full" />
          <SkeletonBox className="h-6 w-20 rounded-full" />
          <SkeletonBox className="h-6 w-16 rounded-full" />
          <SkeletonBox className="h-4 w-full" />
        </div>
      ))}
    </div>
  );
}

/** Full-page skeleton combining all panels */
export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      <OverviewCardsSkeleton />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BuildingSummarySkeleton />
        <GISPanelSkeleton />
      </div>
      <RuleTableSkeleton />
    </div>
  );
}
