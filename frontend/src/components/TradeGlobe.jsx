import React, { useEffect, useRef, useState } from "react";
import Globe from "react-globe.gl";
import { feature as topoFeature, merge as topoMerge } from "topojson-client";

const COUNTRIES_GEOJSON_URL = "https://unpkg.com/world-atlas@2.0.2/countries-110m.json";
// Official India political boundary (includes J&K & Ladakh) — served locally for reliability.
const INDIA_TOPOJSON_URL = "/geo/india-states.json";

const ARCS = [
  // From → To (Indian export routes)
  { startLat: 19.07, startLng: 72.87, endLat: 25.27, endLng: 55.29, color: ["#00C2FF", "#7C3AED"] }, // Mumbai → Dubai
  { startLat: 28.61, startLng: 77.20, endLat: 51.50, endLng: -0.12, color: ["#00C2FF", "#7C3AED"] }, // Delhi → London
  { startLat: 13.08, startLng: 80.27, endLat: 1.35, endLng: 103.81, color: ["#00C2FF", "#7C3AED"] }, // Chennai → Singapore
  { startLat: 22.57, startLng: 88.36, endLat: 35.68, endLng: 139.69, color: ["#00C2FF", "#7C3AED"] }, // Kolkata → Tokyo
  { startLat: 12.97, startLng: 77.59, endLat: 40.71, endLng: -74.00, color: ["#00C2FF", "#7C3AED"] }, // Bengaluru → NYC
  { startLat: 23.02, startLng: 72.57, endLat: 52.52, endLng: 13.40, color: ["#00C2FF", "#7C3AED"] }, // Ahmedabad → Berlin
  { startLat: 17.38, startLng: 78.48, endLat: 31.23, endLng: 121.47, color: ["#00C2FF", "#7C3AED"] }, // Hyderabad → Shanghai
  { startLat: 18.52, startLng: 73.85, endLat: -33.86, endLng: 151.21, color: ["#00C2FF", "#7C3AED"] }, // Pune → Sydney
  { startLat: 19.07, startLng: 72.87, endLat: -23.55, endLng: -46.63, color: ["#00C2FF", "#7C3AED"] }, // Mumbai → São Paulo
  { startLat: 28.61, startLng: 77.20, endLat: 55.75, endLng: 37.61, color: ["#00C2FF", "#7C3AED"] }, // Delhi → Moscow
];

const POINTS = [
  { lat: 19.07, lng: 72.87, label: "Mumbai", size: 0.5 },
  { lat: 28.61, lng: 77.20, label: "Delhi", size: 0.5 },
  { lat: 25.27, lng: 55.29, label: "Dubai", size: 0.4 },
  { lat: 51.50, lng: -0.12, label: "London", size: 0.4 },
  { lat: 1.35, lng: 103.81, label: "Singapore", size: 0.4 },
  { lat: 35.68, lng: 139.69, label: "Tokyo", size: 0.4 },
  { lat: 40.71, lng: -74.00, label: "New York", size: 0.4 },
  { lat: 31.23, lng: 121.47, label: "Shanghai", size: 0.4 },
  { lat: 52.52, lng: 13.40, label: "Berlin", size: 0.4 },
  { lat: -33.86, lng: 151.21, label: "Sydney", size: 0.4 },
  { lat: -23.55, lng: -46.63, label: "São Paulo", size: 0.4 },
  { lat: 55.75, lng: 37.61, label: "Moscow", size: 0.4 },
];

export default function TradeGlobe({ height = 540 }) {
  const globeRef = useRef();
  const wrapRef = useRef();
  const [size, setSize] = useState({ w: 600, h: height });
  const [countries, setCountries] = useState({ features: [] });

  useEffect(() => {
    // Load world basemap + official India boundary in parallel, then splice the
    // correct India polygon (with J&K/Ladakh) over the truncated world-atlas one.
    Promise.all([
      fetch(COUNTRIES_GEOJSON_URL).then((r) => r.json()).catch(() => null),
      fetch(INDIA_TOPOJSON_URL).then((r) => r.json()).catch(() => null),
    ])
      .then(([worldTopo, indiaTopo]) => {
        let features = [];
        if (worldTopo) {
          try {
            const geo = topoFeature(worldTopo, worldTopo.objects.countries);
            // Drop the world-atlas India (wrong northern boundary) — we replace it.
            features = (geo.features || []).filter(
              (f) => f.properties && f.properties.name !== "India"
            );
          } catch (_) {}
        }
        if (indiaTopo && indiaTopo.objects && indiaTopo.objects.states) {
          try {
            const indiaGeom = topoMerge(indiaTopo, indiaTopo.objects.states.geometries);
            features.push({
              type: "Feature",
              properties: { name: "India" },
              geometry: indiaGeom,
            });
          } catch (_) {}
        }
        setCountries({ features });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const update = () => {
      if (wrapRef.current) {
        const w = wrapRef.current.offsetWidth;
        setSize({ w, h: height });
      }
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [height]);

  useEffect(() => {
    if (globeRef.current) {
      const c = globeRef.current.controls();
      c.autoRotate = true;
      c.autoRotateSpeed = 0.55;
      c.enableZoom = false;
      globeRef.current.pointOfView({ lat: 20, lng: 75, altitude: 2.4 }, 0);
    }
  }, []);

  return (
    <div ref={wrapRef} className="globe-wrap relative w-full" style={{ height }}>
      <Globe
        ref={globeRef}
        width={size.w}
        height={size.h}
        backgroundColor="rgba(0,0,0,0)"
        showAtmosphere
        atmosphereColor="#00C2FF"
        atmosphereAltitude={0.22}
        globeImageUrl={null}
        showGlobe={true}
        polygonsData={(countries.features || []).filter(f => f.properties && f.properties.name !== "Antarctica")}
        polygonAltitude={(d) => (d.properties && d.properties.name === "India" ? 0.012 : 0.005)}
        polygonCapColor={(d) => (d.properties && d.properties.name === "India" ? "rgba(124, 58, 237, 0.35)" : "rgba(0, 194, 255, 0.18)")}
        polygonSideColor={(d) => (d.properties && d.properties.name === "India" ? "rgba(124, 58, 237, 0.18)" : "rgba(0, 194, 255, 0.06)")}
        polygonStrokeColor={(d) => (d.properties && d.properties.name === "India" ? "#7C3AED" : "rgba(0, 194, 255, 0.55)")}
        arcsData={ARCS}
        arcColor={"color"}
        arcAltitude={0.25}
        arcStroke={0.45}
        arcDashLength={0.4}
        arcDashGap={1.5}
        arcDashAnimateTime={2200}
        pointsData={POINTS}
        pointColor={() => "#00C2FF"}
        pointAltitude={0.01}
        pointRadius={"size"}
        pointLabel={(p) => `<div style="font-family:'JetBrains Mono';color:#00C2FF;background:rgba(5,8,22,0.9);padding:4px 8px;border:1px solid rgba(0,194,255,0.3);border-radius:8px;font-size:11px">${p.label}</div>`}
        onGlobeReady={() => {
          try {
            if (globeRef.current && typeof globeRef.current.globeMaterial === "function") {
              const globeMat = globeRef.current.globeMaterial();
              if (globeMat) {
                globeMat.color && globeMat.color.set("#0a2540");
                globeMat.emissive && globeMat.emissive.set("#0a2540");
                globeMat.emissiveIntensity = 0.15;
                globeMat.shininess = 12;
              }
            }
          } catch (_) {}
        }}
      />
      {/* Soft halo overlay */}
      <div className="pointer-events-none absolute inset-0 rounded-full" style={{
        background: "radial-gradient(circle at 50% 50%, transparent 50%, rgba(5,8,22,0.6) 80%)"
      }} />
    </div>
  );
}
