/**
 * IFC Parser Demo Page — Module 1
 *
 * Full pipeline: upload .ifc → parse → display BuildingInfo,
 * ElementCounts, and GeometryInfo in a visually rich dashboard.
 */

"use client";

import { useState, useCallback, useRef } from "react";
import { uploadIFC, parseIFC } from "@/services/api";
import type { ParseResult, UploadIFCResponse } from "@/types";
import { AxiosError } from "axios";

// ── Stage machine ─────────────────────────────────────────────────
type Stage = "idle" | "uploading" | "uploaded" | "parsing" | "done" | "error";

export default function ParserPage() {
  const [stage, setStage] = useState<Stage>("idle");
  const [progress, setProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadIFCResponse | null>(null);
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── File selection ─────────────────────────────────────────────
  const handleFile = useCallback((file: File) => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (ext !== ".ifc") {
      setErrorMsg(`Only .ifc files are supported. Got: ${ext}`);
      setStage("error");
      return;
    }
    setErrorMsg(null);
    setSelectedFile(file);
    setUploadResult(null);
    setParseResult(null);
    setStage("idle");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  // ── Upload ─────────────────────────────────────────────────────
  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;
    try {
      setStage("uploading");
      setProgress(0);
      const res = await uploadIFC(selectedFile, setProgress);
      setUploadResult(res);
      setStage("uploaded");
    } catch (err) {
      const msg =
        (err as AxiosError<{ detail?: string }>).response?.data?.detail ||
        (err as Error).message ||
        "Upload failed";
      setErrorMsg(msg);
      setStage("error");
    }
  }, [selectedFile]);

  // ── Parse ──────────────────────────────────────────────────────
  const handleParse = useCallback(async () => {
    if (!uploadResult) return;
    try {
      setStage("parsing");
      const res = await parseIFC(uploadResult.file_id);
      setParseResult(res);
      setStage("done");
    } catch (err) {
      const msg =
        (err as AxiosError<{ detail?: string }>).response?.data?.detail ||
        (err as Error).message ||
        "Parse failed";
      setErrorMsg(msg);
      setStage("error");
    }
  }, [uploadResult]);

  const handleReset = useCallback(() => {
    setStage("idle");
    setSelectedFile(null);
    setUploadResult(null);
    setParseResult(null);
    setErrorMsg(null);
    setProgress(0);
    setShowRaw(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  return (
    <div className="page-container">
      <div className="section-container py-16">
        {/* ── Header ─────────────────────────────────────────── */}
        <div className="max-w-3xl mx-auto text-center mb-12">
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold tracking-wider uppercase mb-6"
            style={{
              background: "rgba(6, 182, 212, 0.1)",
              border: "1px solid rgba(6, 182, 212, 0.25)",
              color: "var(--accent-cyan)",
            }}
          >
            <span>⚙</span> Module 1 — IFC Parser
          </div>

          <h1
            className="text-4xl sm:text-5xl font-bold mb-4"
            style={{ color: "var(--text-primary)" }}
          >
            IFC{" "}
            <span
              style={{
                background: "var(--gradient-primary)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Parser Demo
            </span>
          </h1>
          <p style={{ color: "var(--text-muted)" }} className="text-base leading-relaxed">
            Upload an IFC file to extract building metadata, element counts, and
            geometry — powered by IfcOpenShell on the backend.
          </p>
        </div>

        {/* ── Step indicator ──────────────────────────────────── */}
        <StepIndicator stage={stage} />

        {/* ── Drop zone / interaction cards ───────────────────── */}
        <div className="max-w-2xl mx-auto mt-10">
          {(stage === "idle" || stage === "error") && (
            <DropZone
              isDragging={isDragging}
              selectedFile={selectedFile}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              onUpload={handleUpload}
              onReset={handleReset}
            />
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept=".ifc"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />

          {stage === "uploading" && (
            <UploadingCard filename={selectedFile?.name ?? ""} progress={progress} />
          )}

          {stage === "uploaded" && uploadResult && (
            <UploadedCard result={uploadResult} onParse={handleParse} onReset={handleReset} />
          )}

          {stage === "parsing" && (
            <ParsingCard filename={uploadResult?.filename ?? ""} />
          )}

          {stage === "error" && errorMsg && (
            <ErrorCard message={errorMsg} onReset={handleReset} />
          )}
        </div>

        {/* ── Results Dashboard ───────────────────────────────── */}
        {stage === "done" && parseResult && (
          <ResultDashboard
            result={parseResult}
            filename={uploadResult?.filename ?? ""}
            showRaw={showRaw}
            onToggleRaw={() => setShowRaw((p) => !p)}
            onReset={handleReset}
          />
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// Step Indicator
// ══════════════════════════════════════════════════════════════════

function StepIndicator({ stage }: { stage: Stage }) {
  const steps = ["Select File", "Upload", "Parse", "Results"];
  const activeIndex: Record<Stage, number> = {
    idle: 0, error: 0, uploading: 1, uploaded: 1, parsing: 2, done: 3,
  };
  const active = activeIndex[stage] ?? 0;

  return (
    <div className="flex items-center justify-center max-w-sm mx-auto">
      {steps.map((label, i) => (
        <div key={label} className="flex items-center">
          <div className="flex flex-col items-center gap-1">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300"
              style={{
                background:
                  i < active
                    ? "var(--accent-teal)"
                    : i === active
                    ? "linear-gradient(135deg, #8b5cf6, #06b6d4)"
                    : "rgba(255,255,255,0.06)",
                color: i <= active ? "#fff" : "var(--text-muted)",
                boxShadow: i === active ? "0 0 18px rgba(139,92,246,0.4)" : "none",
              }}
            >
              {i < active ? "✓" : i + 1}
            </div>
            <span
              className="text-xs whitespace-nowrap"
              style={{ color: i <= active ? "var(--text-primary)" : "var(--text-muted)" }}
            >
              {label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div
              className="h-px w-10 sm:w-16 mx-1 mb-4 transition-all duration-500"
              style={{
                background: i < active ? "var(--accent-teal)" : "rgba(255,255,255,0.08)",
              }}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// DropZone
// ══════════════════════════════════════════════════════════════════

function DropZone({
  isDragging, selectedFile, onDragOver, onDragLeave, onDrop, onClick, onUpload, onReset,
}: {
  isDragging: boolean;
  selectedFile: File | null;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onClick: () => void;
  onUpload: () => void;
  onReset: () => void;
}) {
  const fmt = (b: number) =>
    b < 1048576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1048576).toFixed(1)} MB`;

  return (
    <div className="space-y-4">
      {/* Drop target */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={onClick}
        className="dropzone"
        style={{
          border: isDragging
            ? "2px dashed var(--accent-cyan)"
            : "2px dashed rgba(139,92,246,0.3)",
          background: isDragging ? "rgba(6,182,212,0.04)" : undefined,
          cursor: "pointer",
          transition: "all 0.2s ease",
          padding: "3rem 2rem",
          textAlign: "center",
        }}
      >
        <div className="text-5xl mb-4 select-none">🏗️</div>
        <p className="font-semibold text-lg mb-1" style={{ color: "var(--text-primary)" }}>
          {isDragging ? "Drop your IFC file here" : "Drag & drop your IFC file"}
        </p>
        <p className="text-sm mb-5" style={{ color: "var(--text-muted)" }}>
          or click to browse — only <strong style={{ color: "var(--accent-purple)" }}>.ifc</strong> files accepted
        </p>
        <span
          className="px-4 py-1.5 rounded-full text-xs font-bold tracking-wider"
          style={{
            background: "rgba(139,92,246,0.12)",
            color: "var(--accent-purple)",
            border: "1px solid rgba(139,92,246,0.25)",
          }}
        >
          .IFC
        </span>
      </div>

      {/* Selected file row */}
      {selectedFile && (
        <div
          className="glass-card p-4 flex items-center justify-between"
          style={{ border: "1px solid rgba(139,92,246,0.2)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
              style={{ background: "rgba(139,92,246,0.1)" }}
            >
              📄
            </div>
            <div>
              <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>
                {selectedFile.name}
              </p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {fmt(selectedFile.size)}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              id="parser-upload-btn"
              onClick={(e) => { e.stopPropagation(); onUpload(); }}
              className="btn-primary text-sm px-4 py-2"
            >
              Upload ↑
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onReset(); }}
              className="text-xs px-3 py-1.5 rounded-lg transition-colors"
              style={{
                background: "rgba(255,255,255,0.05)",
                color: "var(--text-muted)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// State cards
// ══════════════════════════════════════════════════════════════════

function UploadingCard({ filename, progress }: { filename: string; progress: number }) {
  return (
    <div className="glass-card p-6" style={{ border: "1px solid rgba(139,92,246,0.2)" }}>
      <div className="flex items-center gap-3 mb-4">
        <svg className="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="var(--accent-purple)" strokeWidth="3" opacity="0.3" />
          <path d="M12 2a10 10 0 0 1 10 10" stroke="var(--accent-purple)" strokeWidth="3" strokeLinecap="round" />
        </svg>
        <span className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
          Uploading {filename}…
        </span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${progress}%`, background: "var(--gradient-primary)" }}
        />
      </div>
      <p className="text-right text-xs mt-1" style={{ color: "var(--text-muted)" }}>{progress}%</p>
    </div>
  );
}

function UploadedCard({
  result, onParse, onReset,
}: {
  result: UploadIFCResponse;
  onParse: () => void;
  onReset: () => void;
}) {
  return (
    <div className="glass-card p-6 space-y-5" style={{ border: "1px solid rgba(20,184,166,0.25)" }}>
      <div className="flex items-center gap-2">
        <span className="text-xl">✅</span>
        <span className="font-semibold text-sm" style={{ color: "var(--accent-teal)" }}>
          Upload complete — ready to parse
        </span>
      </div>

      <div
        className="rounded-xl p-4 grid grid-cols-1 gap-2"
        style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
      >
        {[
          { label: "File", value: result.filename },
          { label: "File ID", value: result.file_id },
          { label: "Status", value: result.status },
        ].map((item) => (
          <div key={item.label} className="flex items-baseline gap-2">
            <p className="text-xs w-14 shrink-0" style={{ color: "var(--text-muted)" }}>{item.label}</p>
            <p className="text-xs font-mono truncate" style={{ color: "var(--text-primary)" }}>
              {item.value}
            </p>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <button
          id="parser-parse-btn"
          onClick={onParse}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
          style={{ padding: "0.75rem 1.5rem" }}
        >
          ⚡ Parse IFC File
        </button>
        <button
          onClick={onReset}
          className="text-sm px-4 py-2 rounded-xl"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            color: "var(--text-muted)",
          }}
        >
          Reset
        </button>
      </div>
    </div>
  );
}

function ParsingCard({ filename }: { filename: string }) {
  return (
    <div
      className="glass-card p-10 flex flex-col items-center text-center"
      style={{ border: "1px solid rgba(139,92,246,0.2)" }}
    >
      <div className="relative mb-6">
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center text-4xl"
          style={{ background: "rgba(139,92,246,0.08)", border: "2px solid rgba(139,92,246,0.25)" }}
        >
          🏗️
        </div>
        <svg
          className="absolute -top-2 -right-2 animate-spin"
          width="30" height="30" viewBox="0 0 24 24" fill="none"
        >
          <circle cx="12" cy="12" r="10" stroke="var(--accent-purple)" strokeWidth="3" opacity="0.2" />
          <path d="M12 2a10 10 0 0 1 10 10" stroke="var(--accent-purple)" strokeWidth="3" strokeLinecap="round" />
        </svg>
      </div>
      <h3 className="text-lg font-bold mb-2" style={{ color: "var(--text-primary)" }}>
        Parsing {filename}
      </h3>
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        IfcOpenShell is extracting building metadata, element counts, and geometry…
      </p>
      <div className="flex gap-1.5 mt-6">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full"
            style={{
              background: "var(--accent-purple)",
              animation: `bounce 1s ease-in-out ${i * 0.15}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function ErrorCard({ message, onReset }: { message: string; onReset: () => void }) {
  return (
    <div
      className="p-5 rounded-2xl flex items-start gap-3 mt-4"
      style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}
    >
      <span className="text-xl">⚠️</span>
      <div className="flex-1">
        <p className="font-semibold text-sm mb-1" style={{ color: "#fca5a5" }}>Error</p>
        <p className="text-sm" style={{ color: "rgba(252,165,165,0.8)" }}>{message}</p>
      </div>
      <button
        onClick={onReset}
        className="text-xs px-3 py-1.5 rounded-lg shrink-0"
        style={{ background: "rgba(239,68,68,0.15)", color: "#fca5a5" }}
      >
        Try Again
      </button>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// Result Dashboard
// ══════════════════════════════════════════════════════════════════

function ResultDashboard({
  result, filename, showRaw, onToggleRaw, onReset,
}: {
  result: ParseResult;
  filename: string;
  showRaw: boolean;
  onToggleRaw: () => void;
  onReset: () => void;
}) {
  const { building, elements, geometry } = result;
  const totalElements = Object.values(elements).reduce((a, b) => a + b, 0);

  return (
    <div className="max-w-5xl mx-auto mt-10 space-y-6">
      {/* Success banner */}
      <div
        className="glass-card p-5 flex items-center justify-between flex-wrap gap-3"
        style={{ border: "1px solid rgba(20,184,166,0.25)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: "rgba(20,184,166,0.1)" }}
          >
            ✅
          </div>
          <div>
            <p className="font-bold text-sm" style={{ color: "var(--accent-teal)" }}>Parse Complete</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              {filename} · {totalElements} elements extracted
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onToggleRaw}
            className="text-xs px-3 py-1.5 rounded-lg transition-colors"
            style={{
              background: showRaw ? "rgba(139,92,246,0.15)" : "rgba(255,255,255,0.05)",
              border: "1px solid rgba(139,92,246,0.25)",
              color: "var(--accent-purple)",
            }}
          >
            {showRaw ? "Hide JSON" : "View Raw JSON"}
          </button>
          <button
            onClick={onReset}
            className="text-xs px-3 py-1.5 rounded-lg"
            style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "var(--text-muted)",
            }}
          >
            Parse Another
          </button>
        </div>
      </div>

      {/* Raw JSON */}
      {showRaw && (
        <div className="glass-card p-5" style={{ border: "1px solid rgba(139,92,246,0.2)" }}>
          <p className="text-xs font-semibold mb-3" style={{ color: "var(--accent-purple)" }}>
            Raw ParseResult JSON Contract
          </p>
          <pre
            className="text-xs overflow-auto rounded-xl p-4"
            style={{
              background: "#050810",
              color: "#a3e635",
              border: "1px solid rgba(255,255,255,0.06)",
              maxHeight: "400px",
              fontFamily: "monospace",
            }}
          >
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}

      {/* Three-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <BuildingCard building={building} />
        <ElementsCard elements={elements} totalElements={totalElements} />
        <GeometryCard geometry={geometry} />
      </div>

      {/* Bar chart */}
      <ElementBreakdown elements={elements} totalElements={totalElements} />
    </div>
  );
}

// ── Building metadata card ─────────────────────────────────────
function BuildingCard({ building }: { building: ParseResult["building"] }) {
  const rows = [
    { label: "Project", value: building.project_name, icon: "🏢" },
    { label: "Building", value: building.building_name, icon: "🏛️" },
    { label: "Site", value: building.site_name, icon: "📍" },
    { label: "Schema", value: building.ifc_schema, icon: "📋" },
    { label: "Storeys", value: String(building.storeys), icon: "📐" },
    { label: "Units", value: building.units, icon: "📏" },
    { label: "Owner", value: building.owner, icon: "👤" },
  ];
  return (
    <div className="glass-card p-5" style={{ border: "1px solid rgba(139,92,246,0.2)" }}>
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: "rgba(139,92,246,0.12)" }}>🏗️</div>
        <h2 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>Building Info</h2>
      </div>
      <div className="space-y-2.5">
        {rows.map(({ label, value, icon }) => (
          <div key={label} className="flex items-start gap-2 pb-2.5" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <span className="mt-0.5">{icon}</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{label}</p>
              <p className="text-sm font-medium truncate" style={{ color: value ? "var(--text-primary)" : "var(--text-muted)", fontStyle: value ? "normal" : "italic" }}>
                {value ?? "—"}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Element counts card ────────────────────────────────────────
function ElementsCard({ elements, totalElements }: { elements: ParseResult["elements"]; totalElements: number }) {
  const top3 = Object.entries(elements).sort((a, b) => b[1] - a[1]).slice(0, 3).filter(([, v]) => v > 0);
  return (
    <div className="glass-card p-5" style={{ border: "1px solid rgba(6,182,212,0.2)" }}>
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: "rgba(6,182,212,0.12)" }}>🧱</div>
        <h2 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>Element Counts</h2>
      </div>
      <div className="rounded-xl p-4 mb-4 text-center" style={{ background: "linear-gradient(135deg,rgba(6,182,212,0.08),rgba(139,92,246,0.08))", border: "1px solid rgba(6,182,212,0.15)" }}>
        <p className="text-5xl font-black mb-1" style={{ background: "var(--gradient-primary)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>{totalElements}</p>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>Total Elements</p>
      </div>
      <div className="space-y-2">
        {top3.length === 0 && (
          <p className="text-xs italic text-center" style={{ color: "var(--text-muted)" }}>No elements found</p>
        )}
        {top3.map(([key, val]) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-xs capitalize px-2 py-1 rounded-full" style={{ background: "rgba(6,182,212,0.08)", color: "var(--accent-cyan)", border: "1px solid rgba(6,182,212,0.15)" }}>{key}</span>
            <span className="text-sm font-bold tabular-nums" style={{ color: "var(--text-primary)" }}>{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Geometry card ──────────────────────────────────────────────
function GeometryCard({ geometry }: { geometry: ParseResult["geometry"] }) {
  const hasGeometry = geometry.gross_floor_area !== null || geometry.height !== null || geometry.footprint !== null;
  const metrics = [
    { label: "Floor Area", value: geometry.gross_floor_area !== null ? geometry.gross_floor_area.toFixed(1) : null, unit: "m²", icon: "📐" },
    { label: "Height", value: geometry.height !== null ? geometry.height.toFixed(1) : null, unit: "m", icon: "📏" },
    { label: "Footprint", value: geometry.footprint !== null ? geometry.footprint.toFixed(1) : null, unit: "m²", icon: "🗺️" },
    { label: "Storeys", value: geometry.storey_heights ? String(geometry.storey_heights.length) : null, unit: "", icon: "🏢" },
  ];
  return (
    <div className="glass-card p-5" style={{ border: "1px solid rgba(20,184,166,0.2)" }}>
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: "rgba(20,184,166,0.12)" }}>📐</div>
        <h2 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>Geometry</h2>
      </div>
      {!hasGeometry ? (
        <div className="rounded-xl p-5 text-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px dashed rgba(255,255,255,0.08)" }}>
          <p className="text-3xl mb-2">📦</p>
          <p className="text-sm font-semibold mb-1" style={{ color: "var(--text-secondary)" }}>No 3D Geometry</p>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>This IFC file has no 3D representation. Geometry fields are null by design — no crash, just null.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {metrics.map(({ label, value, unit, icon }) => (
            <div key={label} className="rounded-xl p-3 text-center" style={{ background: "rgba(20,184,166,0.06)", border: "1px solid rgba(20,184,166,0.12)" }}>
              <p className="text-lg mb-1">{icon}</p>
              <p className="text-xl font-black" style={{ color: value ? "var(--accent-teal)" : "var(--text-muted)" }}>
                {value ?? "—"}{value && unit ? <span className="text-xs font-normal ml-0.5">{unit}</span> : null}
              </p>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{label}</p>
            </div>
          ))}
        </div>
      )}
      {geometry.bounding_box && (
        <div className="mt-4 rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
          <p className="text-xs font-semibold mb-2" style={{ color: "var(--text-muted)" }}>Bounding Box (m)</p>
          <div className="grid grid-cols-3 gap-1 text-xs text-center">
            {(["x", "y", "z"] as const).map((axis) => {
              const bb = geometry.bounding_box!;
              const size = ((bb[`max_${axis}` as keyof typeof bb] as number) - (bb[`min_${axis}` as keyof typeof bb] as number)).toFixed(1);
              return (
                <div key={axis}>
                  <p style={{ color: "var(--text-muted)" }}>{axis.toUpperCase()}</p>
                  <p className="font-bold" style={{ color: "var(--accent-teal)" }}>{size}m</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Element breakdown bar chart ────────────────────────────────
const ELEMENT_COLORS: Record<string, string> = {
  walls: "#8b5cf6", doors: "#06b6d4", windows: "#14b8a6",
  slabs: "#3b82f6", columns: "#ec4899", beams: "#f59e0b",
  roofs: "#10b981", stairs: "#f97316", spaces: "#6366f1", openings: "#84cc16",
};
const ELEMENT_ICONS: Record<string, string> = {
  walls: "🧱", doors: "🚪", windows: "🪟", slabs: "⬛",
  columns: "🏛️", beams: "━", roofs: "🏠", stairs: "🪜",
  spaces: "📦", openings: "🔲",
};

function ElementBreakdown({ elements, totalElements }: { elements: ParseResult["elements"]; totalElements: number }) {
  const sorted = Object.entries(elements).sort((a, b) => b[1] - a[1]);
  const maxVal = sorted[0]?.[1] || 1;

  return (
    <div className="glass-card p-6" style={{ border: "1px solid rgba(139,92,246,0.15)" }}>
      <div className="flex items-center gap-2 mb-6">
        <span className="text-xl">📊</span>
        <h2 className="font-bold" style={{ color: "var(--text-primary)" }}>Element Breakdown</h2>
        <span className="ml-auto text-xs px-2 py-1 rounded-full" style={{ background: "rgba(139,92,246,0.1)", color: "var(--accent-purple)" }}>
          {totalElements} total
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
        {sorted.map(([key, value]) => {
          const pct = totalElements === 0 ? 0 : (value / maxVal) * 100;
          const color = ELEMENT_COLORS[key] ?? "#8b5cf6";
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="text-base w-6 text-center shrink-0">{ELEMENT_ICONS[key] ?? "🔷"}</span>
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className="text-xs capitalize font-medium" style={{ color: "var(--text-secondary)" }}>{key}</span>
                  <span className="text-xs font-bold tabular-nums" style={{ color: value > 0 ? color : "var(--text-muted)" }}>{value}</span>
                </div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, background: value > 0 ? color : "transparent" }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
