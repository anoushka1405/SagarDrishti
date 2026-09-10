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
    '1': '#0284c7',
    '3': '#2563eb',
    '6': '#4f46e5',
    '12': '#7c3aed',
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="glass-panel p-5 rounded-2xl border border-blue-300/80 bg-gradient-to-r from-blue-100/90 via-sky-50/90 to-indigo-100/80 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-extrabold text-blue-950 font-heading">
              Drift Physics Simulation Sandbox
            </h2>
            <span className="text-[10px] bg-blue-100 text-blue-950 px-2.5 py-0.5 rounded-full border border-blue-300 font-bold">
              Hydrodynamic Particle Advection
            </span>
          </div>
          <p className="text-xs text-blue-900 max-w-3xl font-medium">
            Experiment with wind drift coupling factors, particle density, and surface ocean current dynamics to model slick deformation.
          </p>
        </div>

        <button
          onClick={handleRunSimulation}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-700 via-indigo-600 to-blue-800 hover:from-blue-600 hover:to-indigo-500 text-white font-bold text-xs shadow-md shadow-blue-700/25 transition-all disabled:opacity-50 border border-blue-400/40"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          <span>Execute Simulation</span>
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="glass-panel p-4 rounded-2xl border border-red-300 bg-red-50 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-800">Simulation Error</p>
            <p className="text-xs text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Grid: Left Controls (4 cols) vs Right Interactive Map (8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Panel */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-5 rounded-2xl border border-blue-200/90 bg-white/95 space-y-5 shadow-md">
            <h3 className="text-sm font-bold text-blue-950 font-heading flex items-center gap-2 border-b border-blue-200/80 pb-3">
              <Sliders className="w-4 h-4 text-blue-600" />
              Physics Parameters
            </h3>

            {/* Slider 1: Wind Drift Factor */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-blue-950 font-bold flex items-center gap-1.5">
                  <Wind className="w-3.5 h-3.5 text-blue-600" />
                  Wind Drift Factor (C_w):
                </span>
                <span className="font-mono text-blue-800 font-extrabold">{(windDriftFactor * 100).toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="0.05"
                step="0.005"
                value={windDriftFactor}
                onChange={(e) => setWindDriftFactor(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-blue-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-[10px] text-blue-800/80 font-mono">
                <span>1% (Light oil)</span>
                <span>3% (Heavy Crude)</span>
                <span>5% (Thin film)</span>
              </div>
            </div>

            {/* Slider 2: Particle Count */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-blue-950 font-bold">Particle Cloud Density (N):</span>
                <span className="font-mono text-blue-800 font-extrabold">{particlesCount} particles</span>
              </div>
              <input
                type="range"
                min="100"
                max="2000"
                step="100"
                value={particlesCount}
                onChange={(e) => setParticlesCount(parseInt(e.target.value, 10))}
                className="w-full h-1.5 bg-blue-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-[10px] text-blue-800/80 font-mono">
                <span>100 (Fast)</span>
                <span>500 (Balanced)</span>
                <span>2000 (High Precision)</span>
              </div>
            </div>

            {/* Formula Explainer Box */}
            <div className="p-3.5 bg-blue-100/80 rounded-xl border border-blue-300 text-[11px] text-slate-800 space-y-1 font-mono">
              <div className="font-bold text-blue-950 font-sans text-xs">Hydrodynamic Equation:</div>
              <div className="font-bold text-blue-900">v_drift = v_current + C_w • v_wind</div>
              <div className="text-[10px] text-blue-950/80 font-sans mt-1">
                Where C_w represents the wind leeway transfer coefficient (typically 3% for marine heavy crude).
              </div>
            </div>
          </div>

          {/* Hindcast Info Panel */}
          {hindcast && (
            <div className="glass-panel p-4 rounded-2xl border border-blue-200/90 bg-white/95 shadow-md">
              <h4 className="text-xs font-bold text-amber-800 flex items-center gap-1.5 mb-2 font-heading">
                <Target className="w-3.5 h-3.5 text-amber-600" />
                Backward Hindcast Results
              </h4>
              <div className="grid grid-cols-2 gap-3 text-[11px]">
                <div className="bg-blue-100/70 rounded-xl p-2.5 border border-blue-200">
                  <span className="text-blue-900/80 block font-medium">Origin Lat</span>
                  <span className="text-blue-950 font-mono font-bold">{hindcast.estimated_origin[0].toFixed(4)}</span>
                </div>
                <div className="bg-blue-100/70 rounded-xl p-2.5 border border-blue-200">
                  <span className="text-blue-900/80 block font-medium">Origin Lon</span>
                  <span className="text-blue-950 font-mono font-bold">{hindcast.estimated_origin[1].toFixed(4)}</span>
                </div>
                <div className="bg-blue-100/70 rounded-xl p-2.5 border border-blue-200">
                  <span className="text-blue-900/80 block font-medium">Uncertainty</span>
                  <span className="text-amber-800 font-mono font-bold">+/-{hindcast.origin_uncertainty_km.toFixed(1)} km</span>
                </div>
                <div className="bg-blue-100/70 rounded-xl p-2.5 border border-blue-200">
                  <span className="text-blue-900/80 block font-medium">Release Window</span>
                  <span className="text-blue-950 font-mono font-bold text-[10px]">
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
            <h3 className="text-sm font-bold text-blue-950 font-heading flex items-center gap-2">
              <Compass className="w-4 h-4 text-blue-600" />
              Simulated Particle Dispersion Cone
            </h3>
            <span className="text-[11px] text-blue-900/80 font-medium">
              Forecast Timeline: +1h (Sky), +3h (Blue), +6h (Indigo), +12h (Purple)
            </span>
          </div>

          <div className="relative w-full h-[500px] rounded-2xl overflow-hidden border border-blue-200 glass-panel shadow-sm">
            <MapContainer center={center} zoom={9} scrollWheelZoom={true} className="w-full h-full">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Forecast Particles */}
              {Object.entries(forecastTracks).map(([hr, pts]) => {
                const color = forecastColors[hr] || '#2563eb';
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
                          fillOpacity: 0.45,
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
                  pathOptions={{ color: '#d97706', weight: 3, dashArray: '8 6', opacity: 0.9 }}
                />
              )}

              {/* Hindcast: estimated origin marker */}
              {hindcast?.estimated_origin && (
                <CircleMarker
                  center={hindcast.estimated_origin}
                  radius={8}
                  pathOptions={{ color: '#d97706', fillColor: '#d97706', fillOpacity: 0.9, weight: 2 }}
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
                  pathOptions={{ color: '#d97706', weight: 1, fillColor: '#d97706', fillOpacity: 0.1, dashArray: '4 4' }}
                />
              )}
            </MapContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
