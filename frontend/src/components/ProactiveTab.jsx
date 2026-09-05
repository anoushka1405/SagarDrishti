import React, { useState, useEffect } from 'react';
import { ShieldAlert, MapPin, AlertCircle, CheckCircle2, Radio, Compass, RefreshCw } from 'lucide-react';
import { MapContainer, TileLayer, Circle, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

function createSanctuaryVesselIcon(score) {
  const isHigh = score >= 50;
  const color = isHigh ? '#ff4d4d' : '#10b981';
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"></circle>
      <polygon points="12 6 15 14 12 12 9 14 12 6" fill="${color}"></polygon>
    </svg>
  `;
  return L.divIcon({
    html: svg,
    className: 'custom-proactive-vessel',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

export default function ProactiveTab({ proactiveData, loading, onRefresh }) {
  const sensitiveZones = proactiveData?.sensitive_zones || [];
  const watchlist = proactiveData?.watchlist || [];

  return (
    <div className="space-y-6">
      {/* Top USP Banner */}
      <div className="glass-panel p-5 rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-slate-900/90 to-teal-500/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-bold text-white font-heading">
              🌟 USP Feature: Proactive Maritime Surveillance
            </h2>
            <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/40 font-mono">
              Continuous Risk Watchlist
            </span>
          </div>
          <p className="text-xs text-slate-300 max-w-3xl">
            Instead of reactively analyzing after an oil spill occurs, SagarDrishti continuously monitors vessels inside 
            environmentally sensitive marine sanctuaries. Suspicious maneuvers (unexpected stops, sharp heading turns, AIS signal dark gaps) trigger immediate alerts.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-teal-300 text-xs font-semibold transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Watchlist</span>
        </button>
      </div>

      {/* Sensitive Zones Cards Row */}
      <div>
        <h3 className="text-sm font-semibold text-white font-heading mb-3 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-teal-400" />
          Protected Eco-Sensitive Marine Reserves
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sensitiveZones.map((zone) => (
            <div
              key={zone.id || zone.name}
              className="glass-panel p-4 rounded-xl border border-slate-800 hover:border-teal-500/40 transition-all text-center space-y-1.5"
            >
              <div className="text-xs font-bold text-teal-300 font-heading truncate">{zone.name}</div>
              <div className="text-[11px] text-slate-400 font-mono">
                ({zone.lat.toFixed(2)}°N, {zone.lon.toFixed(2)}°E)
              </div>
              <div className="text-[10px] text-slate-300 inline-block px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                Protection Radius: R={zone.radius_km} km
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Proactive GIS Map & Live Alerts Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Map View (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white font-heading flex items-center gap-2">
              <Compass className="w-4 h-4 text-teal-400" />
              Sanctuary Surveillance Map
            </h3>
            <span className="text-[11px] text-slate-400">Live Vessel Positions</span>
          </div>

          <div className="relative w-full h-[480px] rounded-2xl overflow-hidden border border-slate-800 glass-panel">
            <MapContainer
              center={[14.5, 72.5]}
              zoom={6}
              scrollWheelZoom={true}
              className="w-full h-full"
            >
              <TileLayer
                attribution='&copy; Esri World Imagery'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              />

              {/* Render Sanctuary Circles */}
              {sensitiveZones.map((zone) => (
                <Circle
                  key={zone.name}
                  center={[zone.lat, zone.lon]}
                  radius={zone.radius_km * 1000}
                  pathOptions={{
                    color: '#2dd4bf',
                    weight: 1.5,
                    dashArray: '4, 4',
                    fillColor: '#2dd4bf',
                    fillOpacity: 0.1,
                  }}
                >
                  <Popup>
                    <div className="p-1 font-sans">
                      <div className="font-bold text-teal-300 text-xs">{zone.name}</div>
                      <div className="text-[11px] text-slate-300">Protected Marine Reserve</div>
                    </div>
                  </Popup>
                </Circle>
              ))}

              {/* Render Watchlist Vessels */}
              {watchlist.map((item) => {
                const score = item.risk_score;
                const pos = item.mmsi === 'SYN-998822101' ? [10.51, 72.52] : item.mmsi === 'SYN-774411993' ? [18.92, 72.82] : [10.45, 72.38];
                return (
                  <Marker
                    key={item.mmsi}
                    position={pos}
                    icon={createSanctuaryVesselIcon(score)}
                  >
                    <Popup>
                      <div className="p-1">
                        <div className="font-bold text-white text-xs font-mono">MMSI: {item.mmsi}</div>
                        <div className="text-[11px] text-teal-300 font-semibold mt-0.5">
                          Zone: {item.zone}
                        </div>
                        <div className="text-[11px] text-amber-300 mt-0.5">
                          Behavioral Anomaly Score: {score.toFixed(0)}/100
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
            </MapContainer>
          </div>
        </div>

        {/* Right Watchlist Alerts Panel (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white font-heading flex items-center gap-2">
                <Radio className="w-4 h-4 text-rose-400 animate-pulse" />
                Active Vessel Surveillance Alerts
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                {watchlist.length} Monitored
              </span>
            </div>

            <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
              {watchlist.map((item) => {
                const score = item.risk_score;
                const isCritical = score >= 50;

                return (
                  <div
                    key={item.mmsi}
                    className={`glass-panel rounded-xl p-4 border transition-all ${
                      isCritical
                        ? 'border-rose-500/50 bg-rose-500/5 shadow-red-glow'
                        : 'border-slate-800 bg-slate-950/60'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white font-mono">MMSI: {item.mmsi}</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            isCritical
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          }`}
                        >
                          {isCritical ? 'CRITICAL ALERT' : 'NORMAL TRANSIT'}
                        </span>
                      </div>

                      <div className={`text-base font-bold font-heading ${isCritical ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {score.toFixed(0)} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 mt-1">
                      Zone: <b className="text-teal-300">{item.zone}</b> | Type: <b className="text-slate-200">{item.vessel_type || 'Tanker'}</b>
                    </div>

                    {/* Evidence Bullets */}
                    <div className="mt-3 pt-2 border-t border-slate-800/80 space-y-1">
                      {item.evidence && item.evidence.length > 0 ? (
                        item.evidence.map((ev, idx) => (
                          <div key={idx} className="text-xs text-rose-300/90 flex items-start gap-1.5">
                            <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                            <span>{ev}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-emerald-400 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Vessel transiting normally with zero behavioral anomalies.</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
