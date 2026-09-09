import React, { useState } from 'react';
import { FlaskConical, Sliders, Play, Wind, Compass, RefreshCw, AlertCircle, Target } from 'lucide-react';
import { MapContainer, TileLayer, Circle, Polyline, CircleMarker, Tooltip } from 'react-leaflet';

export default function SandboxTab() {
  const [particlesCount, setParticlesCount] = useState(500);
  const [windDriftFactor, setWindDriftFactor] = useState(0.03);
  const [loading, setLoading] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [error, setError] = useState(null);

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/simulate_drift', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          n_particles: particlesCount,
          wind_drift_factor: windDriftFactor,
          hindcast_hours: [1, 3, 6],
          forecast_hours: [1, 3, 6, 12],
        }),
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errBody.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      setSimulationData(data);
    } catch (err) {
      console.error('Simulation error:', err);
      setError(err.message || 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const center = simulationData?.center || [18.43, 70.82];
  const forecastTracks = simulationData?.forecast_tracks || {};
  const hindcast = simulationData?.hindcast || null;

  const forecastColors = {
    '1': '#2dd4bf',
    '3': '#38bdf8',
    '6': '#818cf8',
    '12': '#c084fc',
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold text-white font-heading">
              Drift Physics Simulation Sandbox
            </h2>
            <span className="text-[10px] bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded border border-cyan-500/40 font-mono">
              Hydrodynamic Particle Advection
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Experiment with wind drift coupling factors, particle density, and surface ocean current dynamics to model slick deformation.
          </p>
        </div>

          <button
          onClick={handleRunSimulation}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-teal-glow transition-all disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          <span>Execute Simulation</span>
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="glass-panel p-4 rounded-2xl border border-red-500/40 bg-red-500/10 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-300">Simulation Error</p>
            <p className="text-xs text-red-400/80">{error}</p>
          </div>
        </div>
      )}

      {/* Grid: Left Controls (4 cols) vs Right Interactive Map (8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Panel */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-5">
            <h3 className="text-sm font-semibold text-white font-heading flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-teal-400" />
              Physics Parameters
            </h3>

            {/* Slider 1: Wind Drift Factor */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1.5">
                  <Wind className="w-3.5 h-3.5 text-cyan-400" />
                  Wind Drift Factor (C_w):
                </span>
                <span className="font-mono text-cyan-300 font-bold">{(windDriftFactor * 100).toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="0.05"
                step="0.005"
                value={windDriftFactor}
                onChange={(e) => setWindDriftFactor(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-teal-400"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>1% (Light oil)</span>
                <span>3% (Standard Heavy Crude)</span>
                <span>5% (Thin film)</span>
              </div>
            </div>

            {/* Slider 2: Particle Count */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300">Particle Cloud Density (N):</span>
                <span className="font-mono text-teal-300 font-bold">{particlesCount} particles</span>
              </div>
              <input
                type="range"
                min="100"
                max="2000"
                step="100"
                value={particlesCount}
                onChange={(e) => setParticlesCount(parseInt(e.target.value, 10))}
                className="w-full h-1.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-teal-400"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>100 (Fast)</span>
                <span>500 (Balanced)</span>
                <span>2000 (High Precision)</span>
              </div>
            </div>

            {/* Formula Explainer Box */}
            <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1 font-mono">
              <div className="font-semibold text-teal-300 font-sans text-xs">Hydrodynamic Equation:</div>
              <div>v_drift = v_current + C_w • v_wind</div>
              <div className="text-[10px] text-slate-500 font-sans mt-1">
                Where C_w represents the wind leeway transfer coefficient (typically 3% for marine heavy crude).
              </div>
            </div>
          </div>

          {/* Hindcast Info Panel */}
          {hindcast && (
            <div className="glass-panel p-4 rounded-2xl border border-slate-800">
              <h4 className="text-xs font-semibold text-orange-400 flex items-center gap-1.5 mb-2">
                <Target className="w-3.5 h-3.5" />
                Backward Hindcast Results
              </h4>
              <div className="grid grid-cols-2 gap-3 text-[11px]">
                <div className="bg-slate-950/60 rounded-lg p-2">
                  <span className="text-slate-500 block">Origin Lat</span>
                  <span className="text-white font-mono font-bold">{hindcast.estimated_origin[0].toFixed(4)}</span>
                </div>
                <div className="bg-slate-950/60 rounded-lg p-2">
                  <span className="text-slate-500 block">Origin Lon</span>
                  <span className="text-white font-mono font-bold">{hindcast.estimated_origin[1].toFixed(4)}</span>
                </div>
                <div className="bg-slate-950/60 rounded-lg p-2">
                  <span className="text-slate-500 block">Uncertainty</span>
                  <span className="text-orange-300 font-mono font-bold">+/-{hindcast.origin_uncertainty_km.toFixed(1)} km</span>
                </div>
                <div className="bg-slate-950/60 rounded-lg p-2">
                  <span className="text-slate-500 block">Release Window</span>
                  <span className="text-white font-mono font-bold text-[10px]">
                    {hindcast.release_window[0].slice(11, 16)} – {hindcast.release_window[1].slice(11, 16)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Map View */}
        <div className="lg:col-span-8 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white font-heading flex items-center gap-2">
              <Compass className="w-4 h-4 text-teal-400" />
              Simulated Particle Dispersion Cone
            </h3>
            <span className="text-[11px] text-slate-400">
              Forecast Timeline: +1h (Teal), +3h (Cyan), +6h (Blue), +12h (Purple)
            </span>
          </div>

          <div className="relative w-full h-[500px] rounded-2xl overflow-hidden border border-slate-800 glass-panel">
            <MapContainer center={center} zoom={9} scrollWheelZoom={true} className="w-full h-full">
              <TileLayer
                attribution='&copy; Esri World Imagery'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              />

              {/* Forecast Particles */}
              {Object.entries(forecastTracks).map(([hr, pts]) => {
                const color = forecastColors[hr] || '#38bdf8';
                return (
                  <React.Fragment key={hr}>
                    {(pts || []).slice(0, 300).map((pt, idx) => (
                      <Circle
                        key={`sim-${hr}-${idx}`}
                        center={[pt[0], pt[1]]}
                        radius={150}
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

              {/* Hindcast: backward drift track */}
              {hindcast?.track && hindcast.track.length > 1 && (
                <Polyline
                  positions={hindcast.track}
                  pathOptions={{ color: '#f97316', weight: 3, dashArray: '8 6', opacity: 0.9 }}
                />
              )}

              {/* Hindcast: estimated origin marker */}
              {hindcast?.estimated_origin && (
                <CircleMarker
                  center={hindcast.estimated_origin}
                  radius={8}
                  pathOptions={{ color: '#f97316', fillColor: '#f97316', fillOpacity: 0.9, weight: 2 }}
                >
                  <Tooltip direction="top" offset={[0, -8]} permanent>
                    <span style={{ fontWeight: 700, fontSize: 11 }}>
                      Est. Origin ({hindcast.estimated_origin[0].toFixed(3)}, {hindcast.estimated_origin[1].toFixed(3)})
                    </span>
                  </Tooltip>
                </CircleMarker>
              )}

              {/* Hindcast: uncertainty radius */}
              {hindcast?.estimated_origin && hindcast?.origin_uncertainty_km && (
                <Circle
                  center={hindcast.estimated_origin}
                  radius={hindcast.origin_uncertainty_km * 1000}
                  pathOptions={{ color: '#f97316', weight: 1, fillColor: '#f97316', fillOpacity: 0.08, dashArray: '4 4' }}
                />
              )}
            </MapContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
