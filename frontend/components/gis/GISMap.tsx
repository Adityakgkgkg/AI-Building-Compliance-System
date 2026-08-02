/**
 * GIS Interactive Leaflet Map Component
 * =====================================
 * Client-side Leaflet map rendered inside Next.js with SSR safety.
 * Restricts viewport to Greater Bangalore bounds, handles click-to-pick marker placement,
 * and renders interactive GeoJSON layers (Wards, Roads, Lakes, Airport Buffer).
 */

"use client";

import { useEffect, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";

interface LocationPreset {
  name: string;
  lat: number;
  lon: number;
  description: string;
}

export const BANGALORE_PRESETS: LocationPreset[] = [
  { name: "Jayanagar 4th Block", lat: 12.9250, lon: 77.5938, description: "Ward 167 - South Zone" },
  { name: "Indiranagar 100ft Road", lat: 12.9719, lon: 77.6412, description: "Ward 112 - East Zone" },
  { name: "Koramangala 5th Block", lat: 12.9352, lon: 77.6245, description: "Ward 151 - South Zone" },
  { name: "Whitefield ITPL Main Rd", lat: 12.9840, lon: 77.7315, description: "Ward 82 - Mahadevapura" },
  { name: "Yelahanka Satellite Town", lat: 13.1005, lon: 77.5963, description: "Ward 35 - Yelahanka" },
  { name: "MG Road Commercial Axis", lat: 12.9750, lon: 77.6050, description: "Ward 149 - Central Axis" },
  { name: "Bellandur Lake Vicinity", lat: 12.9360, lon: 77.6720, description: "Water Buffer Zone" },
];

interface GISMapProps {
  latitude: number;
  longitude: number;
  onLocationSelect: (lat: number, lon: number) => void;
  activeLayers: {
    wards: boolean;
    roads: boolean;
    lakes: boolean;
    airport: boolean;
    landuse: boolean;
  };
  layersGeoJSON: {
    wards?: any;
    roads?: any;
    lakes?: any;
    airport?: any;
    landuse?: any;
  };
}

export default function GISMap({
  latitude,
  longitude,
  onLocationSelect,
  activeLayers,
  layersGeoJSON,
}: GISMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const geojsonLayersRef = useRef<{ [key: string]: any }>({});
  const [L, setL] = useState<any>(null);

  // Dynamically import Leaflet on client side
  useEffect(() => {
    import("leaflet").then((leafletModule) => {
      setL(leafletModule.default || leafletModule);
    });
  }, []);

  // Initialize Map
  useEffect(() => {
    if (!L || !mapContainerRef.current || mapInstanceRef.current) return;

    // Bangalore bounds: SW (12.80, 77.40), NE (13.18, 77.80)
    const bangaloreBounds = L.latLngBounds(
      L.latLng(12.80, 77.40),
      L.latLng(13.18, 77.80)
    );

    const map = L.map(mapContainerRef.current, {
      center: [latitude, longitude],
      zoom: 12,
      minZoom: 10,
      maxZoom: 18,
      maxBounds: bangaloreBounds,
      maxBoundsViscosity: 0.8,
    });

    // Dark Matter tile layer for premium visual aesthetics
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 19,
      }
    ).addTo(map);

    // Click handler to pick location
    map.on("click", (e: any) => {
      const { lat, lng } = e.latlng;
      // Ensure clicked point is within Bangalore bounds
      if (lat >= 12.80 && lat <= 13.20 && lng >= 77.40 && lng <= 77.80) {
        onLocationSelect(Number(lat.toFixed(6)), Number(lng.toFixed(6)));
      }
    });

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [L]);

  // Update Marker Location
  useEffect(() => {
    if (!L || !mapInstanceRef.current) return;

    const customIcon = L.divIcon({
      className: "custom-gis-marker",
      html: `
        <div style="
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #8b5cf6;
          border: 3px solid #ffffff;
          box-shadow: 0 0 15px rgba(139, 92, 246, 0.8);
          position: relative;
        ">
          <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ffffff;
          "></div>
        </div>
      `,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    if (markerRef.current) {
      markerRef.current.setLatLng([latitude, longitude]);
    } else {
      markerRef.current = L.marker([latitude, longitude], { icon: customIcon }).addTo(
        mapInstanceRef.current
      );
    }

    mapInstanceRef.current.panTo([latitude, longitude], { animate: true });
  }, [L, latitude, longitude]);

  // Render / Toggle GeoJSON Layers
  useEffect(() => {
    if (!L || !mapInstanceRef.current) return;

    const map = mapInstanceRef.current;

    const layerConfigs: { [key: string]: { active: boolean; data: any; style: any } } = {
      wards: {
        active: activeLayers.wards,
        data: layersGeoJSON.wards,
        style: {
          color: "#3b82f6",
          weight: 2,
          opacity: 0.8,
          fillColor: "#3b82f6",
          fillOpacity: 0.15,
        },
      },
      roads: {
        active: activeLayers.roads,
        data: layersGeoJSON.roads,
        style: {
          color: "#f59e0b",
          weight: 4,
          opacity: 0.9,
        },
      },
      lakes: {
        active: activeLayers.lakes,
        data: layersGeoJSON.lakes,
        style: {
          color: "#06b6d4",
          weight: 2,
          opacity: 0.9,
          fillColor: "#06b6d4",
          fillOpacity: 0.35,
        },
      },
      airport: {
        active: activeLayers.airport,
        data: layersGeoJSON.airport,
        style: {
          color: "#ef4444",
          weight: 2,
          dashArray: "5, 5",
          opacity: 0.8,
          fillColor: "#ef4444",
          fillOpacity: 0.15,
        },
      },
      landuse: {
        active: activeLayers.landuse,
        data: layersGeoJSON.landuse,
        style: {
          color: "#10b981",
          weight: 1,
          opacity: 0.6,
          fillColor: "#10b981",
          fillOpacity: 0.12,
        },
      },
    };

    Object.entries(layerConfigs).forEach(([key, cfg]) => {
      // Remove layer if toggled off
      if (geojsonLayersRef.current[key]) {
        map.removeLayer(geojsonLayersRef.current[key]);
        delete geojsonLayersRef.current[key];
      }

      // Add layer if active and data exists
      if (cfg.active && cfg.data) {
        const geoLayer = L.geoJSON(cfg.data, {
          style: cfg.style,
          onEachFeature: (feature: any, layer: any) => {
            const props = feature.properties || {};
            const popupContent = Object.entries(props)
              .map(([k, v]) => `<strong>${k}:</strong> ${v}`)
              .join("<br/>");
            layer.bindPopup(`<div style="font-family: sans-serif; font-size: 12px; color: #1e293b;">${popupContent}</div>`);
          },
        }).addTo(map);

        geojsonLayersRef.current[key] = geoLayer;
      }
    });
  }, [L, activeLayers, layersGeoJSON]);

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-2xl border border-slate-700/50">
      <div ref={mapContainerRef} className="w-full h-full min-h-[500px] z-10" />

      {/* Preset Location Quick Selector Header Overlay */}
      <div className="absolute top-4 left-4 z-20 glass p-2 rounded-xl flex items-center gap-2 max-w-full overflow-x-auto shadow-lg bg-slate-900/85 text-xs text-white border border-slate-700">
        <span className="font-semibold px-2 py-1 text-slate-400">Presets:</span>
        {BANGALORE_PRESETS.map((preset) => (
          <button
            key={preset.name}
            onClick={() => onLocationSelect(preset.lat, preset.lon)}
            className={`px-3 py-1.5 rounded-lg whitespace-nowrap font-medium transition-all ${
              latitude === preset.lat && longitude === preset.lon
                ? "bg-purple-600 text-white shadow-md shadow-purple-500/30"
                : "bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white"
            }`}
          >
            {preset.name}
          </button>
        ))}
      </div>
    </div>
  );
}
