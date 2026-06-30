/**
 * About Page
 *
 * Project description, objectives, tech stack, and team info.
 */

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About",
  description:
    "About the AI-Driven Building Plan Compliance and 3D Urban Integration system.",
};

export default function AboutPage() {
  return (
    <div className="page-container">
      <div className="section-container py-16">
        {/* ── Header ───────────────────────────────────────── */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold tracking-wider uppercase mb-6 animate-fade-in"
            style={{
              background: "rgba(20, 184, 166, 0.1)",
              border: "1px solid rgba(20, 184, 166, 0.2)",
              color: "var(--accent-teal)",
            }}
          >
            About the Project
          </div>

          <h1
            className="text-3xl sm:text-4xl font-bold mb-6 animate-fade-in-up"
            style={{ color: "var(--text-primary)" }}
          >
            AI-Driven{" "}
            <span className="gradient-text">Context-Aware</span>{" "}
            Building Compliance
          </h1>

          <p
            className="text-base leading-relaxed animate-fade-in-up delay-100 opacity-0"
            style={{ color: "var(--text-muted)", animationFillMode: "forwards" }}
          >
            A final year AI & ML project that aims to revolutionize building
            plan compliance checking through artificial intelligence, geographic
            information systems, and immersive 3D visualization.
          </p>
        </div>

        {/* ── Content Grid ─────────────────────────────────── */}
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Project Overview */}
          <div className="glass-card p-8 animate-fade-in-up delay-200 opacity-0" style={{ animationFillMode: "forwards" }}>
            <h2
              className="text-xl font-bold mb-4 flex items-center gap-3"
              style={{ color: "var(--text-primary)" }}
            >
              <span
                className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                style={{ background: "rgba(139, 92, 246, 0.1)" }}
              >
                🎯
              </span>
              Project Overview
            </h2>
            <p
              className="leading-relaxed"
              style={{ color: "var(--text-secondary)" }}
            >
              Traditional building plan compliance checking is a manual,
              time-consuming process prone to human error. This project
              develops an AI-driven system that automates the entire workflow
              — from parsing building plans in IFC/DXF formats, to checking
              them against building codes, to visualizing them in a 3D urban
              context with GIS data integration.
            </p>
          </div>

          {/* Objectives */}
          <div className="glass-card p-8 animate-fade-in-up delay-300 opacity-0" style={{ animationFillMode: "forwards" }}>
            <h2
              className="text-xl font-bold mb-6 flex items-center gap-3"
              style={{ color: "var(--text-primary)" }}
            >
              <span
                className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                style={{ background: "rgba(6, 182, 212, 0.1)" }}
              >
                🚀
              </span>
              Key Objectives
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {objectives.map((obj, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold"
                    style={{
                      background: "var(--gradient-primary)",
                      color: "white",
                    }}
                  >
                    {i + 1}
                  </div>
                  <p
                    className="text-sm leading-relaxed"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {obj}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Tech Stack */}
          <div className="glass-card p-8 animate-fade-in-up delay-400 opacity-0" style={{ animationFillMode: "forwards" }}>
            <h2
              className="text-xl font-bold mb-6 flex items-center gap-3"
              style={{ color: "var(--text-primary)" }}
            >
              <span
                className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                style={{ background: "rgba(20, 184, 166, 0.1)" }}
              >
                ⚡
              </span>
              Technology Stack
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {stackCategories.map((cat) => (
                <div key={cat.title}>
                  <h3
                    className="text-sm font-semibold mb-3 uppercase tracking-wider"
                    style={{ color: cat.color }}
                  >
                    {cat.title}
                  </h3>
                  <div className="space-y-2">
                    {cat.items.map((item) => (
                      <div
                        key={item}
                        className="flex items-center gap-2 text-sm"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ background: cat.color }}
                        />
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Roadmap */}
          <div className="glass-card p-8 animate-fade-in-up delay-500 opacity-0" style={{ animationFillMode: "forwards" }}>
            <h2
              className="text-xl font-bold mb-6 flex items-center gap-3"
              style={{ color: "var(--text-primary)" }}
            >
              <span
                className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                style={{ background: "rgba(236, 72, 153, 0.1)" }}
              >
                📅
              </span>
              Development Roadmap
            </h2>
            <div className="space-y-4">
              {roadmap.map((sprint, i) => (
                <div key={i} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <div
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{
                        background: sprint.active
                          ? "var(--accent-purple)"
                          : "var(--border-subtle)",
                        boxShadow: sprint.active
                          ? "0 0 12px rgba(139, 92, 246, 0.5)"
                          : "none",
                      }}
                    />
                    {i < roadmap.length - 1 && (
                      <div
                        className="w-px h-full min-h-[2rem]"
                        style={{ background: "var(--border-subtle)" }}
                      />
                    )}
                  </div>
                  <div className="pb-4">
                    <div className="flex items-center gap-2">
                      <h3
                        className="text-sm font-semibold"
                        style={{
                          color: sprint.active
                            ? "var(--accent-purple)"
                            : "var(--text-primary)",
                        }}
                      >
                        {sprint.title}
                      </h3>
                      {sprint.active && (
                        <span
                          className="text-[0.6rem] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full"
                          style={{
                            background: "rgba(139, 92, 246, 0.15)",
                            color: "var(--accent-purple)",
                          }}
                        >
                          Current
                        </span>
                      )}
                    </div>
                    <p
                      className="text-xs mt-1"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {sprint.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Data ─────────────────────────────────────────────────────────
const objectives = [
  "Automate IFC/DXF file parsing and data extraction",
  "Implement AI-driven compliance checking against building codes",
  "Integrate GIS data for context-aware urban analysis",
  "Develop interactive 3D visualization of building models",
  "Generate comprehensive compliance reports with AI recommendations",
  "Build a scalable, production-ready full-stack platform",
];

const stackCategories = [
  {
    title: "Frontend",
    color: "#8b5cf6",
    items: ["Next.js (App Router)", "React", "TypeScript", "Tailwind CSS", "Axios"],
  },
  {
    title: "Backend",
    color: "#06b6d4",
    items: ["FastAPI", "Python", "Uvicorn", "Pydantic", "SQLAlchemy"],
  },
  {
    title: "Database",
    color: "#14b8a6",
    items: ["SQLite (Development)", "SQLAlchemy ORM"],
  },
  {
    title: "AI & Tools",
    color: "#ec4899",
    items: ["IFC Parser (Sprint 2)", "GIS Engine (Sprint 4)", "ML Models (Sprint 5)"],
  },
];

const roadmap = [
  {
    title: "Sprint 1 — Foundation",
    description:
      "Project scaffolding, API setup, UI design system, upload functionality.",
    active: true,
  },
  {
    title: "Sprint 2 — IFC Parsing",
    description:
      "IFC/DXF file parsing, building data extraction, metadata storage.",
    active: false,
  },
  {
    title: "Sprint 3 — Compliance Engine",
    description:
      "Rule-based compliance checking, building code validation, reporting.",
    active: false,
  },
  {
    title: "Sprint 4 — GIS Integration",
    description:
      "Geographic context analysis, zoning data, urban density metrics.",
    active: false,
  },
  {
    title: "Sprint 5 — AI & 3D",
    description:
      "AI-powered recommendations, 3D visualization, final integration.",
    active: false,
  },
];
