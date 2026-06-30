/**
 * DashboardCard Component
 *
 * Reusable glassmorphism card for the Dashboard page.
 * Displays an icon, title, description, and optional "Coming Soon" badge.
 */

interface DashboardCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  accentColor: string;
  comingSoon?: boolean;
  delay?: number;
}

export default function DashboardCard({
  title,
  description,
  icon,
  accentColor,
  comingSoon = true,
  delay = 0,
}: DashboardCardProps) {
  return (
    <div
      className="glass-card p-6 animate-fade-in-up opacity-0"
      style={{
        animationDelay: `${delay}ms`,
        animationFillMode: "forwards",
      }}
    >
      {/* ── Icon ─────────────────────────────────────────────── */}
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
        style={{
          background: `${accentColor}15`,
          color: accentColor,
        }}
      >
        {icon}
      </div>

      {/* ── Content ──────────────────────────────────────────── */}
      <h3
        className="text-lg font-semibold mb-2"
        style={{ color: "var(--text-primary)" }}
      >
        {title}
      </h3>
      <p
        className="text-sm leading-relaxed mb-4"
        style={{ color: "var(--text-muted)" }}
      >
        {description}
      </p>

      {/* ── Badge ────────────────────────────────────────────── */}
      {comingSoon && (
        <div className="coming-soon-badge animate-pulse-glow">
          <span
            className="w-1.5 h-1.5 rounded-full inline-block"
            style={{ background: accentColor }}
          />
          Coming Soon
        </div>
      )}
    </div>
  );
}
