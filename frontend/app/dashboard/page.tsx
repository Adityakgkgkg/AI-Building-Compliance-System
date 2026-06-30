/**
 * Dashboard Page
 *
 * Placeholder cards for future modules:
 * Building Info, Compliance, GIS, 3D Viewer, Report.
 * All display "Coming Soon".
 */

import type { Metadata } from "next";
import DashboardCard from "@/components/DashboardCard";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Dashboard overview of building compliance analysis modules.",
};

export default function DashboardPage() {
  return (
    <div className="page-container">
      <div className="section-container py-16">
        {/* ── Header ───────────────────────────────────────── */}
        <div className="mb-12">
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold tracking-wider uppercase mb-6 animate-fade-in"
            style={{
              background: "rgba(6, 182, 212, 0.1)",
              border: "1px solid rgba(6, 182, 212, 0.2)",
              color: "var(--accent-cyan)",
            }}
          >
            <svg
              width="14"
              height="14"
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
          </div>

          <h1
            className="text-3xl sm:text-4xl font-bold mb-4 animate-fade-in-up"
            style={{ color: "var(--text-primary)" }}
          >
            Analysis{" "}
            <span className="gradient-text">Dashboard</span>
          </h1>
          <p
            className="text-base max-w-2xl animate-fade-in-up delay-100 opacity-0"
            style={{ color: "var(--text-muted)", animationFillMode: "forwards" }}
          >
            All compliance analysis modules will be accessible here. Each card
            below represents a module that will be implemented in upcoming sprints.
          </p>
        </div>

        {/* ── Cards Grid ───────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Building Information */}
          <DashboardCard
            title="Building Information"
            description="View parsed building metadata, structural data, floor plans, and dimensional analysis from uploaded IFC/DXF files."
            accentColor="#8b5cf6"
            delay={200}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4" />
                <path d="M9 9v.01M9 12v.01M9 15v.01M9 18v.01" />
              </svg>
            }
          />

          {/* Compliance Check */}
          <DashboardCard
            title="Compliance Check"
            description="Run automated compliance checks against building codes and regulations. Get detailed pass/fail reports with actionable insights."
            accentColor="#06b6d4"
            delay={300}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M9 11l3 3L22 4" />
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
              </svg>
            }
          />

          {/* GIS Context */}
          <DashboardCard
            title="GIS Context"
            description="Analyze geographic context, zoning data, surrounding infrastructure, and urban density metrics for comprehensive site analysis."
            accentColor="#14b8a6"
            delay={400}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            }
          />

          {/* 3D Viewer */}
          <DashboardCard
            title="3D Viewer"
            description="Interactive 3D visualization of building models within their urban environment. Navigate, rotate, and inspect every detail."
            accentColor="#ec4899"
            delay={500}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2l9 4.5v11L12 22l-9-4.5v-11L12 2z" />
                <path d="M12 22V11M12 11L3 6.5M12 11l9-4.5" />
              </svg>
            }
          />

          {/* Report */}
          <DashboardCard
            title="Compliance Report"
            description="Generate comprehensive PDF reports with compliance results, AI recommendations, and visual summaries for stakeholders."
            accentColor="#f59e0b"
            delay={600}
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            }
          />
        </div>
      </div>
    </div>
  );
}
