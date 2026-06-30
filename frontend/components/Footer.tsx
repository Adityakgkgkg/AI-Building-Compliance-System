/**
 * Footer Component
 *
 * Site-wide footer with project info and links.
 */

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="mt-auto py-8"
      style={{
        borderTop: "1px solid var(--border-subtle)",
        background: "rgba(10, 14, 26, 0.6)",
      }}
    >
      <div className="section-container">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* ── Brand ───────────────────────────────────────── */}
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs"
              style={{ background: "var(--gradient-primary)" }}
            >
              AI
            </div>
            <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              AI Building Compliance System
            </span>
          </div>

          {/* ── Info ────────────────────────────────────────── */}
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            © {currentYear} Final Year AI & ML Project. Built with Next.js & FastAPI.
          </p>
        </div>
      </div>
    </footer>
  );
}
