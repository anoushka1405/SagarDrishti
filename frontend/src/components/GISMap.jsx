import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, Circle, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Navigation, AlertTriangle, ShieldCheck, Ship } from 'lucide-react';

// Custom vessel marker icons factory
function createVesselIcon(score) {
  const isHigh = score >= 70;
  const isMedium = score >= 40;
  const colorClass = isHigh ? '#ff4d4d' : isMedium ? '#ffb703' : '#38bdf8';
  const glowColor = isHigh ? 'rgba(255, 77, 77, 0.6)' : isMedium ? 'rgba(255, 183, 3, 0.5)' : 'rgba(56, 189, 248, 0.4)';

  const svgIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="${colorClass}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px ${glowColor});">
      <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
    </svg>
  `;

  return L.divAnchor ? L.divIcon({
    html: `<div style="transform: rotate(0deg); display: flex; align-items: center; justify-content: center;">${svgIcon}</div>`,
    className: 'custom-vessel-marker-div',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  }) : L.divIcon({
    html: `<div style="display: flex; align-items: center; justify-content: center;">${svgIcon}</div>`,
    className: 'custom-vessel-marker-div',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, zoom, { animate: true });
    }
  }, [center, zoom, map]);
  return null;
}

export default function GISMap({ pipelineResults, onSelectVessel, selectedVessel }) {
  const centroid = pipelineResults?.centroid || [18.43, 70.82];
  const origin = pipelineResults?.estimated_origin || centroid;
  const uncertaintyKm = pipelineResults?.origin_uncertainty_km || 5.0;
  const polygonCoords = pipelineResults?.spill_polygon_coords || [];
  const hindcastTrack = pipelineResults?.hindcast_track || [];
  const rankedVessels = pipelineResults?.ranked_vessels || [];
  const forecastTracks = pipelineResults?.forecast_tracks || {};

  // Color palette for forecast particle hours
  const forecastColors = {
    '1': '#2dd4bf',
    '3': '#38bdf8',
    '6': '#818cf8',
    '12': '#c084fc',
  };

  return (
    <div className="relative w-full h-[520px] rounded-2xl overflow-hidden border border-slate-800 glass-panel shadow-2xl">
      <MapContainer
        center={centroid}
        zoom={9}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <MapController center={centroid} zoom={9} />

        {/* ESRI World Imagery Satellite & Ocean Map Layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>, Maxar, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />

        {/* Detected Spill Polygon Boundary */}
        {polygonCoords.length > 0 && (
          <Polygon
            positions={polygonCoords}
            pathOptions={{
              color: '#ff4d4d',
              weight: 2.5,
              fillColor: '#ff4d4d',
              fillOpacity: 0.45,
            }}
          />
        )}

        {/* Estimated Spill Origin Uncertainty Radius Circle */}
        {origin && (
          <Circle
            center={origin}
            radius={uncertaintyKm * 1000} // radius in meters
            pathOptions={{
              color: '#ffb703',
              weight: 1.5,
              dashArray: '5, 8',
              fillColor: '#ffb703',
              fillOpacity: 0.12,
            }}
          >
            <Popup>
              <div className="p-1">
                <div className="font-bold text-amber-400 text-xs font-heading">
                  Estimated Origin Centroid
                </div>
                <div className="text-[11px] text-slate-300 font-mono mt-1">
                  Lat: {origin[0].toFixed(4)} N, Lon: {origin[1].toFixed(4)} E
                </div>
                <div className="text-[11px] text-amber-300 mt-1">
                  Uncertainty Radius: ±{uncertaintyKm} km
                </div>
              </div>
            </Popup>
          </Circle>
        )}

        {/* Backward Particle Drift Hindcast Track */}
        {hindcastTrack.length > 1 && (
          <Polyline
            positions={hindcastTrack}
            pathOptions={{
              color: '#00e5ff',
              weight: 2.5,
              dashArray: '6, 6',
            }}
          />
        )}

        {/* Forecast Particle Spread Clouds */}
        {Object.entries(forecastTracks).map(([hr, pts]) => {
          const color = forecastColors[hr] || '#38bdf8';
          return (
            <React.Fragment key={hr}>
              {(pts || []).slice(0, 150).map((pt, idx) => (
                <Circle
                  key={`forecast-${hr}-${idx}`}
                  center={[pt[0], pt[1]]}
                  radius={180}
                  pathOptions={{
                    color: color,
                    weight: 0,
                    fillColor: color,
                    fillOpacity: 0.35,
                  }}
                />
              ))}
            </React.Fragment>
          );
        })}

        {/* Suspect Vessel Markers & Trajectory Polylines */}
        {rankedVessels.map((vessel) => {
          const score = vessel.attribution_score;
          const traj = vessel.trajectory || [];
          const lastPos = traj.length > 0 ? [traj[traj.length - 1][0], traj[traj.length - 1][1]] : null;
          const polyPositions = traj.map((pt) => [pt[0], pt[1]]);

          const isHigh = score >= 70;
          const lineStyle = {
            color: isHigh ? '#ff4d4d' : score >= 40 ? '#ffb703' : '#38bdf8',
            weight: isHigh ? 3 : 2,
            dashArray: isHigh ? undefined : '4, 4',
          };

          return (
            <React.Fragment key={vessel.mmsi}>
              {/* Trajectory Polyline */}
              {polyPositions.length > 1 && (
                <Polyline positions={polyPositions} pathOptions={lineStyle} />
              )}

              {/* Vessel Position Marker */}
              {lastPos && (
                <Marker
                  position={lastPos}
                  icon={createVesselIcon(score)}
                  eventHandlers={{
                    click: () => onSelectVessel && onSelectVessel(vessel),
                  }}
                >
                  <Popup>
                    <div className="w-56 p-1">
                      <div className="flex items-center justify-between border-b border-slate-700/80 pb-1.5 mb-2">
                        <span className="font-bold text-white text-xs font-mono">
                          MMSI: {vessel.mmsi}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            score >= 70
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : score >= 40
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
                          }`}
                        >
                          {vessel.confidence_level} Risk ({score}/100)
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-300 space-y-1">
                        <div>
                          Vessel Type: <b className="text-white">{vessel.vessel_type}</b>
                        </div>
                        <div>
                          Closest Approach: <b className="text-teal-300">{vessel.closest_distance_km} km</b>
                        </div>
                        <div>
                          Release Time Offset: <b className="text-teal-300">{vessel.time_delta_hours} hrs</b>
                        </div>
                      </div>

                      {vessel.evidence && vessel.evidence.length > 0 && (
                        <div className="mt-2 text-[10px] text-slate-400 bg-slate-900/80 p-1.5 rounded border border-slate-800">
                          <div className="font-semibold text-rose-300 mb-0.5">Primary Anomaly:</div>
                          <div>{vessel.evidence[0]}</div>
                        </div>
                      )}
                    </div>
                  </Popup>
                </Marker>
              )}
            </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Map Floating Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] glass-panel px-3 py-2.5 rounded-xl border border-slate-800 text-[11px] space-y-1.5 text-slate-300">
        <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1 mb-1 font-heading">
          GIS Layer Overlay
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-rose-500/70 border border-rose-400 inline-block" />
          <span>Detected Spill Boundary</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full border border-dashed border-amber-400 bg-amber-400/20 inline-block" />
          <span>Estimated Origin Circle (±km)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-4 h-0.5 border-t-2 border-dashed border-cyan-400 inline-block" />
          <span>Backward Drift Track</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" />
          <span>Suspect Vessels (High Attribution)</span>
        </div>
      </div>
    </div>
  );
}
