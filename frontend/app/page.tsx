/**
 * Home Page
 *
 * Professional landing page with hero section, feature highlights,
 * and call-to-action buttons.
 */

import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Home",
  description:
    "AI-Driven Context-Aware System for Automated Building Plan Compliance and 3D Urban Integration.",
};

export default function HomePage() {
  return (
    <div className="page-container">
      {/* ═══════════════════════════════════════════════════════
          HERO SECTION
          ═══════════════════════════════════════════════════════ */}
      <section className="hero-bg relative min-h-[85vh] flex items-center">
        <div className="grid-overlay" />

        {/* Decorative Orbs */}
        <div
          className="absolute top-20 right-[15%] w-72 h-72 rounded-full animate-float opacity-30 blur-3xl"
          style={{ background: "var(--accent-purple)" }}
        />
        <div
          className="absolute bottom-32 left-[10%] w-56 h-56 rounded-full animate-float opacity-20 blur-3xl"
          style={{ background: "var(--accent-cyan)", animationDelay: "2s" }}
        />

        <div className="section-container relative z-10 py-20">
          <div className="max-w-3xl">
            {/* Badge */}
            <div
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold tracking-wider uppercase mb-8 animate-fade-in-up"
              style={{
                background: "rgba(139, 92, 246, 0.1)",
                border: "1px solid rgba(139, 92, 246, 0.2)",
                color: "var(--accent-purple)",
              }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: "var(--accent-teal)" }}
              />
              AI & ML Final Year Project
            </div>

            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6 animate-fade-in-up delay-100 opacity-0" style={{ animationFillMode: "forwards" }}>
              AI-Driven{" "}
              <span className="gradient-text">Building Plan</span>{" "}
              Compliance & 3D Urban Integration
            </h1>

            {/* Description */}
            <p
              className="text-lg sm:text-xl leading-relaxed mb-10 max-w-2xl animate-fade-in-up delay-200 opacity-0"
              style={{ color: "var(--text-secondary)", animationFillMode: "forwards" }}
            >
              A context-aware system that automates building plan compliance
              checking using AI, integrates with GIS data, and provides 3D
              urban visualization for smarter city planning.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4 animate-fade-in-up delay-300 opacity-0" style={{ animationFillMode: "forwards" }}>
              <Link href="/upload" className="btn-primary">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                Upload Plan
              </Link>
              <Link href="/dashboard" className="btn-secondary">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
                Dashboard
              </Link>
              <Link href="/about" className="btn-secondary">
                About Project
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════
          FEATURES SECTION
          ═══════════════════════════════════════════════════════ */}
      <section className="py-24" style={{ background: "var(--bg-secondary)" }}>
        <div className="section-container">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
              What This System Will Do
            </h2>
            <p
              className="max-w-2xl mx-auto text-base"
              style={{ color: "var(--text-muted)" }}
            >
              A comprehensive platform combining AI, GIS, and 3D visualization
              for next-generation urban planning compliance.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className="glass-card p-6 animate-fade-in-up opacity-0"
                style={{
                  animationDelay: `${i * 100 + 200}ms`,
                  animationFillMode: "forwards",
                }}
              >
                <div
                  className="w-11 h-11 rounded-xl flex items-center justify-center mb-4 text-lg"
                  style={{
                    background: `${feature.color}15`,
                    color: feature.color,
                  }}
                >
                  {feature.emoji}
                </div>
                <h3
                  className="font-semibold mb-2"
                  style={{ color: "var(--text-primary)" }}
                >
                  {feature.title}
                </h3>
                <p
                  className="text-sm leading-relaxed"
                  style={{ color: "var(--text-muted)" }}
                >
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════
          TECH STACK SECTION
          ═══════════════════════════════════════════════════════ */}
      <section className="py-24">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
              Built With Modern Technology
            </h2>
          </div>

          <div className="flex flex-wrap justify-center gap-4">
            {techStack.map((tech, i) => (
              <div
                key={tech}
                className="px-5 py-2.5 rounded-xl text-sm font-medium animate-fade-in opacity-0"
                style={{
                  background: "var(--bg-glass)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-secondary)",
                  animationDelay: `${i * 60}ms`,
                  animationFillMode: "forwards",
                }}
              >
                {tech}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

// ── Data ─────────────────────────────────────────────────────────
const features = [
  {
    emoji: "📐",
    title: "IFC/DXF Parsing",
    description:
      "Automatically extract building metadata, dimensions, and structural data from industry-standard file formats.",
    color: "#8b5cf6",
  },
  {
    emoji: "✅",
    title: "Compliance Checking",
    description:
      "AI-powered rule engine that validates building plans against local and national building codes.",
    color: "#06b6d4",
  },
  {
    emoji: "🌍",
    title: "GIS Integration",
    description:
      "Context-aware analysis using geographic data, zoning maps, and surrounding urban infrastructure.",
    color: "#14b8a6",
  },
  {
    emoji: "🏙️",
    title: "3D Visualization",
    description:
      "Interactive 3D rendering of building models integrated within their urban environment.",
    color: "#ec4899",
  },
];

const techStack = [
  "Next.js",
  "React",
  "TypeScript",
  "Tailwind CSS",
  "FastAPI",
  "Python",
  "SQLAlchemy",
  "SQLite",
  "Pydantic",
  "Axios",
];
