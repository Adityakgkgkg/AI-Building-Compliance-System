/**
 * Urban Context Intelligence Engine (UCIE) Dashboard Page
 * =======================================================
 * Production-ready GIS dashboard for municipal building plan approval context analysis.
 */

"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import GISSidebar from "@/components/gis/GISSidebar";
import {
  fetchGISContext,
  fetchGISManifest,
  fetchGISLayer,
  GISContextResponse,
  ManifestData,
} from "@/services/gisService";

// Dynamically import GISMap to disable Next.js SSR for Leaflet
const GISMap = dynamic(() => import("@/components/gis/GISMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] bg-slate-950 flex items-center justify-center text-slate-400 rounded-2xl border border-slate-800">
      <div className="flex items-center gap-3">
        <svg className="animate-spin h-5 w-5 text-purple-500" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <span>Loading Bangalore GIS Map Engine...</span>
      </div>
    </div>
  ),
});

export default function GISPage() {
  // Default location: Jayanagar 4th Block, Bangalore
  const [latitude, setLatitude] = useState<number>(12.9250);
  const [longitude, setLongitude] = useState<number>(77.5938);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [context, setContext] = useState<GISContextResponse | null>(null);
  const [manifest, setManifest] = useState<ManifestData | null>(null);

  const [activeLayers, setActiveLayers] = useState({
    wards: true,
    roads: true,
    lakes: true,
    airport: false,
    landuse: false,
  });

  const [layersGeoJSON, setLayersGeoJSON] = useState<{ [key: string]: any }>({});

  // Initial evaluation on load
  useEffect(() => {
    handleEvaluate(latitude, longitude);
    loadManifest();
  }, []);

  const loadManifest = async () => {
    try {
      const data = await fetchGISManifest();
      setManifest(data);
    } catch (err) {
      console.warn("Failed to load GIS dataset manifest:", err);
    }
  };

  const handleEvaluate = async (lat: number, lon: number) => {
    setIsLoading(true);
    try {
      const res = await fetchGISContext(lat, lon);
      setContext(res);
    } catch (err) {
      console.error("GIS context evaluation failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocationSelect = (lat: number, lon: number) => {
    setLatitude(lat);
    setLongitude(lon);
    handleEvaluate(lat, lon);
  };

  const handleToggleLayer = async (layerName: string) => {
    const nextState = !activeLayers[layerName as keyof typeof activeLayers];
    setActiveLayers((prev) => ({ ...prev, [layerName]: nextState }));

    // Fetch layer GeoJSON if turning on and not already cached
    if (nextState && !layersGeoJSON[layerName]) {
      try {
        const geojson = await fetchGISLayer(layerName);
        setLayersGeoJSON((prev) => ({ ...prev, [layerName]: geojson }));
      } catch (err) {
        console.error(`Failed to fetch GeoJSON for layer ${layerName}:`, err);
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 section-container pt-20 pb-10 flex flex-col gap-6">
        {/* Page Title Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-purple-400 bg-clip-text text-transparent">
              Urban Context Intelligence Engine (UCIE)
            </h1>
            <p className="text-xs md:text-sm text-slate-400 mt-1">
              Automated spatial context resolution for BBMP Bangalore building plan approvals & municipal compliance.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800/50 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              BBMP GIS Verified
            </span>
          </div>
        </div>

        {/* Dashboard Content Layout */}
        <div className="flex flex-col lg:flex-row gap-6 min-h-[600px] flex-1">
          {/* Main Leaflet Map Viewport */}
          <div className="flex-1 w-full min-h-[500px]">
            <GISMap
              latitude={latitude}
              longitude={longitude}
              onLocationSelect={handleLocationSelect}
              activeLayers={activeLayers}
              layersGeoJSON={layersGeoJSON}
            />
          </div>

          {/* Interactive GIS Sidebar */}
          <GISSidebar
            latitude={latitude}
            longitude={longitude}
            onLatitudeChange={setLatitude}
            onLongitudeChange={setLongitude}
            onEvaluate={() => handleEvaluate(latitude, longitude)}
            isLoading={isLoading}
            context={context}
            manifest={manifest}
            activeLayers={activeLayers}
            onToggleLayer={handleToggleLayer}
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}
