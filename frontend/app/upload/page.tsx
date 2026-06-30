/**
 * Upload Page
 *
 * Drag-and-drop file upload interface for IFC/DXF building plans.
 */

import type { Metadata } from "next";
import FileDropzone from "@/components/FileDropzone";

export const metadata: Metadata = {
  title: "Upload",
  description: "Upload IFC or DXF building plan files for compliance analysis.",
};

export default function UploadPage() {
  return (
    <div className="page-container">
      <div className="section-container py-16">
        {/* ── Header ───────────────────────────────────────── */}
        <div className="max-w-2xl mx-auto text-center mb-12">
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold tracking-wider uppercase mb-6 animate-fade-in"
            style={{
              background: "rgba(139, 92, 246, 0.1)",
              border: "1px solid rgba(139, 92, 246, 0.2)",
              color: "var(--accent-purple)",
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
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Upload Module
          </div>

          <h1
            className="text-3xl sm:text-4xl font-bold mb-4 animate-fade-in-up"
            style={{ color: "var(--text-primary)" }}
          >
            Upload Your{" "}
            <span className="gradient-text">Building Plan</span>
          </h1>
          <p
            className="text-base leading-relaxed animate-fade-in-up delay-100 opacity-0"
            style={{ color: "var(--text-muted)", animationFillMode: "forwards" }}
          >
            Upload an IFC or DXF file to get started. In future sprints, the
            system will automatically parse, analyze, and check your building
            plan for compliance.
          </p>
        </div>

        {/* ── Dropzone ─────────────────────────────────────── */}
        <div className="max-w-2xl mx-auto animate-fade-in-up delay-200 opacity-0" style={{ animationFillMode: "forwards" }}>
          <FileDropzone />
        </div>

        {/* ── Info Cards ───────────────────────────────────── */}
        <div className="max-w-2xl mx-auto mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {infoCards.map((card, i) => (
            <div
              key={card.title}
              className="glass-card p-4 text-center animate-fade-in-up opacity-0"
              style={{
                animationDelay: `${300 + i * 100}ms`,
                animationFillMode: "forwards",
              }}
            >
              <div className="text-2xl mb-2">{card.emoji}</div>
              <h3
                className="text-sm font-semibold mb-1"
                style={{ color: "var(--text-primary)" }}
              >
                {card.title}
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {card.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const infoCards = [
  {
    emoji: "📁",
    title: "Supported Formats",
    description: "IFC and DXF files",
  },
  {
    emoji: "📏",
    title: "Max File Size",
    description: "Up to 100 MB",
  },
  {
    emoji: "🔒",
    title: "Secure Upload",
    description: "Files stored safely",
  },
];
