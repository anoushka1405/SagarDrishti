import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, Circle, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Play, Pause, SkipForward, RotateCcw } from 'lucide-react';

// Custom vessel marker icons factory
function createVesselIcon(score) {
  const isHigh = score >= 70;
  const isMedium = score >= 40;
  const colorClass = isHigh ? '#e11d48' : isMedium ? '#d97706' : '#2563eb';
  const glowColor = isHigh ? 'rgba(225, 29, 72, 0.5)' : isMedium ? 'rgba(217, 119, 6, 0.4)' : 'rgba(37, 99, 235, 0.4)';

  const svgIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="${colorClass}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 6px ${glowColor});">
      <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
    </svg>
  `;

  return L.divIcon({
    html: `<div style="transform: rotate(0deg); display: flex; align-items: center; justify-content: center;">${svgIcon}</div>`,
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

  // Color palette for forecast particle hours (Ocean Blue parallel gradient accents)
  const forecastColors = {
    '1': '#0d9488',
    '3': '#0284c7',
    '6': '#4f46e5',
    '12': '#9333ea',
  };

  // Time-slider state
  const timeSteps = ['all', ...Object.keys(forecastTracks).sort((a, b) => Number(a) - Number(b))];
  const [activeStep, setActiveStep] = useState('all');
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef(null);

  const stepIndex = timeSteps.indexOf(activeStep);

  const advanceStep = useCallback(() => {
    setActiveStep((prev) => {
      const idx = timeSteps.indexOf(prev);
      const nextIdx = (idx + 1) % timeSteps.length;
      return timeSteps[nextIdx];
    });
  }, [timeSteps]);

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(advanceStep, 1500);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, advanceStep]);

  const togglePlay = () => setIsPlaying((p) => !p);
  const resetSlider = () => { setIsPlaying(false); setActiveStep('all'); };
  const skipForward = () => {
    setActiveStep((prev) => {
      const idx = timeSteps.indexOf(prev);
      const nextIdx = (idx + 1) % timeSteps.length;
      return timeSteps[nextIdx];
    });
  };

  // Filter forecast tracks based on active time step
  const visibleTracks = activeStep === 'all'
    ? forecastTracks
    : { [activeStep]: forecastTracks[activeStep] };

  return (
    <div className="relative w-full h-[600px] rounded-2xl overflow-hidden border border-blue-200/80 glass-panel shadow-xl">
      <MapContainer
        center={centroid}
        zoom={9}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <MapController center={centroid} zoom={9} />

        {/* ESRI World Imagery Satellite & Ocean Map Layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>, Maxar, GeoEye, Earthstar Geographics'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />

        {/* Detected Spill Polygon Boundary */}
        {polygonCoords.length > 0 && (
          <Polygon
            positions={polygonCoords}
            pathOptions={{
              color: '#e11d48',
              weight: 2.5,
              fillColor: '#f43f5e',
              fillOpacity: 0.5,
            }}
          />
        )}

        {/* Estimated Spill Origin Uncertainty Radius Circle */}
        {origin && (
          <Circle
            center={origin}
            radius={uncertaintyKm * 1000} // radius in meters
            pathOptions={{
              color: '#d97706',
              weight: 1.8,
              dashArray: '5, 8',
              fillColor: '#f59e0b',
              fillOpacity: 0.15,
            }}
          >
            <Popup>
              <div className="p-1 text-slate-800">
                <div className="font-bold text-amber-700 text-xs font-heading">
                  Estimated Origin Centroid
                </div>
                <div className="text-[11px] text-slate-700 font-mono mt-1">
                  Lat: {origin[0].toFixed(4)} N, Lon: {origin[1].toFixed(4)} E
                </div>
                <div className="text-[11px] text-amber-800 font-semibold mt-1">
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
              color: '#0284c7',
              weight: 3,
              dashArray: '6, 6',
            }}
          />
        )}

        {/* Forecast Particle Spread Clouds (filtered by time slider) */}
        {Object.entries(visibleTracks).map(([hr, pts]) => {
          const color = forecastColors[hr] || '#0284c7';
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
                    fillOpacity: 0.4,
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
            color: isHigh ? '#e11d48' : score >= 40 ? '#d97706' : '#2563eb',
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
                    <div className="w-56 p-1 text-slate-800">
                      <div className="flex items-center justify-between border-b border-slate-200 pb-1.5 mb-2">
                        <span className="font-bold text-slate-900 text-xs font-mono">
                          MMSI: {vessel.mmsi}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            score >= 70
                              ? 'bg-rose-100 text-rose-800 border border-rose-300'
                              : score >= 40
                              ? 'bg-amber-100 text-amber-800 border border-amber-300'
                              : 'bg-blue-100 text-blue-800 border border-blue-300'
                          }`}
                        >
                          {vessel.confidence_level} Risk ({score}/100)
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-600 space-y-1">
                        <div>
                          Vessel Type: <b className="text-slate-900">{vessel.vessel_type}</b>
                        </div>
                        <div>
                          Closest Approach: <b className="text-blue-700">{vessel.closest_distance_km} km</b>
                        </div>
                        <div>
                          Release Time Offset: <b className="text-blue-700">{vessel.time_delta_hours} hrs</b>
                        </div>
                      </div>

                      {vessel.evidence && vessel.evidence.length > 0 && (
                        <div className="mt-2 text-[10px] text-slate-600 bg-slate-50 p-1.5 rounded border border-slate-200">
                          <div className="font-semibold text-rose-700 mb-0.5">Primary Anomaly:</div>
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

      {/* Floating Drift Forecast Control Panel Overlay */}
      <div className="absolute top-3 right-3 z-[1000] glass-panel p-3.5 rounded-2xl border border-blue-100 shadow-lg text-xs space-y-2.5 max-w-xs bg-white/95 backdrop-blur-md">
        <div className="flex items-center justify-between border-b border-blue-100 pb-1.5">
          <span className="font-bold text-blue-950 font-heading flex items-center gap-1.5">
            <Play className="w-3.5 h-3.5 text-blue-600" />
            Forward Drift Cone
          </span>
          <span className="text-[10px] text-slate-500 font-mono font-medium">Hydrodynamic</span>
        </div>

        {/* Time Step Buttons */}
        <div className="flex items-center gap-1 bg-blue-50/80 p-1 rounded-xl border border-blue-100">
          <button
            onClick={() => { setIsPlaying(false); setActiveStep('all'); }}
            className={`flex-1 text-[11px] py-1 rounded-lg font-semibold transition-all ${
              activeStep === 'all' ? 'bg-gradient-to-r from-blue-700 to-indigo-600 text-white font-bold shadow-xs' : 'text-slate-600 hover:text-blue-900'
            }`}
          >
            All Tracks
          </button>
          {['1', '3', '6', '12'].map((hrs) => (
            <button
              key={hrs}
              onClick={() => { setIsPlaying(false); setActiveStep(hrs); }}
              className={`text-[11px] px-2 py-1 rounded-lg font-semibold transition-all ${
                activeStep === hrs ? 'bg-gradient-to-r from-blue-700 to-indigo-600 text-white font-bold shadow-xs' : 'text-slate-600 hover:text-blue-900'
              }`}
            >
              +{hrs}h
            </button>
          ))}
        </div>

        {/* Forecast Leg Legend */}
        <div className="grid grid-cols-2 gap-1.5 pt-1 text-[10px] text-slate-700 font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-600" />
            <span>+1h Drift</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-600" />
            <span>+3h Drift</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
            <span>+6h Drift</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-600" />
            <span>+12h Drift</span>
          </div>
        </div>
      </div>

      {/* Floating Interactive Time Slider Controller Overlay */}
      <div className="absolute bottom-3 left-3 right-3 z-[1000] glass-panel p-3.5 rounded-2xl border border-blue-100 shadow-lg bg-white/95 backdrop-blur-md">
        <div className="flex items-center justify-between gap-3">
          {/* Play/Pause */}
          <button
            onClick={togglePlay}
            className="w-8 h-8 flex items-center justify-center rounded-xl bg-gradient-to-r from-blue-700 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-500 transition-colors shadow-xs"
            title={isPlaying ? 'Pause simulation' : 'Play forecast timeline'}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
          </button>

          {/* Step Forward */}
          <button
            onClick={skipForward}
            className="w-8 h-8 flex items-center justify-center rounded-xl bg-blue-50/80 border border-blue-100 text-blue-900 hover:bg-blue-100 transition-colors"
            title="Next step"
          >
            <SkipForward className="w-4 h-4" />
          </button>

          {/* Reset */}
          <button
            onClick={resetSlider}
            className="w-8 h-8 flex items-center justify-center rounded-xl bg-blue-50/80 border border-blue-100 text-blue-900 hover:bg-blue-100 transition-colors"
            title="Show all"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          {/* Slider Track */}
          <div className="flex-1 flex items-center gap-2">
            <input
              type="range"
              min={0}
              max={timeSteps.length - 1}
              step={1}
              value={stepIndex}
              onChange={(e) => {
                setIsPlaying(false);
                setActiveStep(timeSteps[parseInt(e.target.value, 10)]);
              }}
              className="flex-1 h-1.5 bg-blue-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          {/* Current Step Label */}
          <div className="w-24 text-right">
            <span className="text-[11px] font-mono font-bold text-blue-900">
              {activeStep === 'all' ? 'All Hours' : `+${activeStep}h`}
            </span>
          </div>
        </div>

        {/* Step Tick Labels */}
        <div className="flex justify-between mt-1 px-[72px]">
          {timeSteps.map((step) => (
            <button
              key={step}
              onClick={() => { setIsPlaying(false); setActiveStep(step); }}
              className={`text-[9px] font-mono px-1 py-0.5 rounded transition-colors ${
                activeStep === step
                  ? 'text-blue-900 bg-blue-100 font-bold'
                  : 'text-slate-500 hover:text-blue-900'
              }`}
            >
              {step === 'all' ? 'ALL' : `${step}h`}
            </button>
          ))}
        </div>
      </div>

      {/* Map Floating Legend */}
      <div className="absolute bottom-20 left-3 z-[1000] glass-panel px-3.5 py-3 rounded-2xl border border-blue-100 shadow-md text-[11px] space-y-1.5 text-slate-700 bg-white/95 backdrop-blur-md">
        <div className="font-bold text-blue-950 border-b border-blue-100 pb-1 mb-1 font-heading">
          GIS Layer Overlay
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-rose-500/70 border border-rose-600 inline-block" />
          <span>Detected Spill Boundary</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full border border-dashed border-amber-600 bg-amber-400/30 inline-block" />
          <span>Estimated Origin Circle (±km)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-4 h-0.5 border-t-2 border-dashed border-blue-600 inline-block" />
          <span>Backward Drift Track</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-rose-600 inline-block" />
          <span>Suspect Vessels (High Attribution)</span>
        </div>
      </div>
    </div>
  );
}
