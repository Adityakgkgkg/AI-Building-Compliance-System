/**
 * GIS Context Intelligence Sidebar Component
 * ==========================================
 * Interactive sidebar displaying spatial metrics, environmental buffers,
 * statutory height restrictions, layer controls, and municipal approval report text.
 */

"use client";

import { useState } from "react";
import { GISContextResponse, ManifestData } from "@/services/gisService";

interface GISSidebarProps {
  latitude: number;
  longitude: number;
  onLatitudeChange: (lat: number) => void;
  onLongitudeChange: (lon: number) => void;
  onEvaluate: () => void;
  isLoading: boolean;
  context: GISContextResponse | null;
  manifest: ManifestData | null;
  activeLayers: {
    wards: boolean;
    roads: boolean;
    lakes: boolean;
    airport: boolean;
    landuse: boolean;
  };
  onToggleLayer: (layerName: string) => void;
}

export default function GISSidebar({
  latitude,
  longitude,
  onLatitudeChange,
  onLongitudeChange,
  onEvaluate,
  isLoading,
  context,
  manifest,
  activeLayers,
  onToggleLayer,
}: GISSidebarProps) {
  const [activeTab, setActiveTab] = useState<"context" | "report" | "manifest">("context");

  return (
    <div className="w-full lg:w-96 flex flex-col gap-4 bg-slate-900/90 backdrop-blur-md p-5 rounded-2xl border border-slate-800 shadow-xl text-slate-100 h-full max-h-[85vh] overflow-y-auto">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center font-bold text-white text-sm shadow-md shadow-purple-500/20">
            GIS
          </div>
          <div>
            <h2 className="font-semibold text-sm text-white">Urban Context Intelligence</h2>
            <p className="text-[11px] text-slate-400">BBMP Spatial Compliance Engine</p>
          </div>
        </div>
        {context && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-950/80 text-purple-300 border border-purple-800/50">
            {context.execution_time_ms} ms
          </span>
        )}
      </div>

      {/* ── Coordinates Input Form ───────────────────────────── */}
      <div className="flex flex-col gap-2 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
        <label className="text-xs font-medium text-slate-300">Site Coordinates (WGS84)</label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-[10px] text-slate-400 block mb-0.5">Latitude</span>
            <input
              type="number"
              step="0.0001"
              value={latitude}
              onChange={(e) => onLatitudeChange(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 block mb-0.5">Longitude</span>
            <input
              type="number"
              step="0.0001"
              value={longitude}
              onChange={(e) => onLongitudeChange(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>
        </div>
        <button
          onClick={onEvaluate}
          disabled={isLoading}
          className="mt-1 w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold py-2 px-4 rounded-lg transition-all shadow-md shadow-purple-600/20 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Evaluating...
            </>
          ) : (
            "Evaluate Spatial Context"
          )}
        </button>
      </div>

      {/* ── Layer Toggles ────────────────────────────────────── */}
      <div className="flex flex-col gap-1.5 bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
        <span className="text-xs font-medium text-slate-300 mb-1">GIS Map Layers</span>
        <div className="grid grid-cols-3 gap-1.5">
          {[
            { key: "wards", label: "Wards", color: "bg-blue-500" },
            { key: "roads", label: "Roads", color: "bg-amber-500" },
            { key: "lakes", label: "Lakes", color: "bg-cyan-500" },
            { key: "airport", label: "Airport", color: "bg-red-500" },
            { key: "landuse", label: "Land Use", color: "bg-emerald-500" },
          ].map((item) => {
            const isActive = activeLayers[item.key as keyof typeof activeLayers];
            return (
              <button
                key={item.key}
                onClick={() => onToggleLayer(item.key)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium transition-all ${
                  isActive
                    ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                    : "bg-slate-900/50 text-slate-500 border border-transparent hover:text-slate-300"
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${item.color} ${isActive ? "opacity-100" : "opacity-30"}`} />
                {item.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Tabs Navigation ──────────────────────────────────── */}
      <div className="flex border-b border-slate-800 gap-1 text-xs">
        <button
          onClick={() => setActiveTab("context")}
          className={`pb-2 px-3 font-medium transition-all border-b-2 ${
            activeTab === "context"
              ? "border-purple-500 text-purple-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Spatial Context
        </button>
        <button
          onClick={() => setActiveTab("report")}
          className={`pb-2 px-3 font-medium transition-all border-b-2 ${
            activeTab === "report"
              ? "border-purple-500 text-purple-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Approval Report
        </button>
        <button
          onClick={() => setActiveTab("manifest")}
          className={`pb-2 px-3 font-medium transition-all border-b-2 ${
            activeTab === "manifest"
              ? "border-purple-500 text-purple-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Datasets Manifest
        </button>
      </div>

      {/* ── Tab Content: Spatial Context ─────────────────────── */}
      {activeTab === "context" && (
        <div className="flex flex-col gap-2 text-xs">
          {context ? (
            <>
              {/* Containment Status Badge */}
              <div
                className={`p-2.5 rounded-xl border flex items-center justify-between ${
                  context.is_inside_bbmp
                    ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
                    : "bg-amber-950/40 border-amber-800/60 text-amber-300"
                }`}
              >
                <span className="font-semibold text-xs">BBMP Boundary Status</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-900/60 text-emerald-200">
                  {context.is_inside_bbmp ? "INSIDE BBMP" : "OUTSIDE BBMP"}
                </span>
              </div>

              {/* Administrative Information */}
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400">Administrative Boundary</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Zone</span>
                    <span className="font-medium text-white">{context.zone}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Ward</span>
                    <span className="font-medium text-white">
                      {context.ward_number ? `Ward ${context.ward_number} - ${context.ward}` : context.ward}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Authority</span>
                    <span className="font-medium text-white">{context.authority}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Master Plan Zoning</span>
                    <span className="font-medium text-purple-300">{context.land_use}</span>
                  </div>
                </div>
              </div>

              {/* Road & FAR Parameters */}
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400">Adjacent Road & FAR Parameters</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Nearest Road</span>
                    <span className="font-medium text-amber-300">{context.road_name}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Road Width</span>
                    <span className="font-bold text-amber-400 text-sm">{context.road_width} m</span>
                  </div>
                </div>
              </div>

              {/* Environmental Buffer Alerts */}
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400">Environmental Constraints</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Lake Proximity</span>
                    <span className="font-medium text-cyan-300">{context.lake_distance} m</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Lake Buffer Violation</span>
                    <span
                      className={`font-semibold ${
                        context.lake_buffer ? "text-red-400" : "text-emerald-400"
                      }`}
                    >
                      {context.lake_buffer ? "VIOLATION (Restricted)" : "CLEAR (Compliant)"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Storm Drain Distance</span>
                    <span className="font-medium text-slate-200">{context.storm_drain_distance} m</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Flood Risk Level</span>
                    <span
                      className={`font-semibold ${
                        context.flood_risk === "High"
                          ? "text-red-400"
                          : context.flood_risk === "Medium"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {context.flood_risk}
                    </span>
                  </div>
                </div>
              </div>

              {/* Statutory Height Restrictions */}
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400">Statutory Airport Height Zone</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Airport Restriction</span>
                    <span className={`font-semibold ${context.airport_zone ? "text-amber-400" : "text-emerald-400"}`}>
                      {context.airport_zone ? "RESTRICTED FUNNEL" : "UNRESTRICTED"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Height Limitation</span>
                    <span className="font-medium text-white">
                      {context.airport_height_limit ? `${context.airport_height_limit} m AGL` : "No Restriction"}
                    </span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="p-6 text-center text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800">
              Click on the map or click 'Evaluate Spatial Context' to view GIS intelligence.
            </div>
          )}
        </div>
      )}

      {/* ── Tab Content: Approval Report Section ─────────────── */}
      {activeTab === "report" && (
        <div className="flex flex-col gap-3 text-xs">
          {context ? (
            <>
              <div className="bg-purple-950/30 border border-purple-800/40 p-3 rounded-xl">
                <span className="font-semibold text-purple-300 block mb-1">Generated Approval Report Clause</span>
                <p className="text-slate-200 leading-relaxed font-sans text-xs italic">
                  "{context.approval_report_text}"
                </p>
              </div>

              <span className="font-semibold text-slate-300 text-xs">Verifiable Datasets Citations</span>
              <div className="flex flex-col gap-2">
                {context.citations.map((cit, i) => (
                  <div key={i} className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 text-[11px]">
                    <div className="flex justify-between font-semibold text-slate-200 mb-0.5">
                      <span>{cit.dataset_name}</span>
                      <span className="text-purple-400">{cit.authority}</span>
                    </div>
                    <p className="text-slate-400 text-[10px] mb-1">{cit.observation}</p>
                    <a
                      href={cit.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[10px] text-indigo-400 underline hover:text-indigo-300"
                    >
                      {cit.source_url}
                    </a>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="p-6 text-center text-slate-500">No report generated yet.</div>
          )}
        </div>
      )}

      {/* ── Tab Content: Datasets Manifest ────────────────────── */}
      {activeTab === "manifest" && (
        <div className="flex flex-col gap-2 text-xs">
          <span className="font-semibold text-slate-300">Approved Spatial Datasets Lineage</span>
          {manifest && manifest.datasets ? (
            manifest.datasets.map((ds, idx) => (
              <div key={idx} className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 text-[11px] flex flex-col gap-1">
                <div className="flex justify-between font-semibold text-white">
                  <span>{ds.dataset_name}</span>
                  <span className="text-emerald-400 text-[10px]">{ds.status}</span>
                </div>
                <div className="grid grid-cols-2 gap-1 text-[10px] text-slate-400">
                  <span>Authority: {ds.authority}</span>
                  <span>CRS: {ds.coordinate_system}</span>
                  <span>Geometries: {ds.geometry_count}</span>
                  <span>License: {ds.license}</span>
                </div>
                <div className="text-[9px] font-mono text-slate-500 truncate">
                  SHA256: {ds.checksum_sha256}
                </div>
              </div>
            ))
          ) : (
            <div className="p-6 text-center text-slate-500">Loading dataset manifest...</div>
          )}
        </div>
      )}
    </div>
  );
}
