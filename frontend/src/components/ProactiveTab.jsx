import React, { useState, useEffect } from 'react';
import { ShieldAlert, MapPin, AlertCircle, CheckCircle2, Radio, Compass, RefreshCw } from 'lucide-react';
import { MapContainer, TileLayer, Circle, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

function createSanctuaryVesselIcon(score) {
  const isHigh = score >= 50;
  const color = isHigh ? '#e11d48' : '#2563eb';
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
      <div className="glass-panel p-5 rounded-2xl border border-blue-300/80 bg-gradient-to-r from-blue-100/90 via-sky-50/90 to-indigo-100/80 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-600" />
            <h2 className="text-lg font-extrabold text-blue-950 font-heading">
              🌟 Proactive Maritime Surveillance
            </h2>
            <span className="text-[10px] bg-amber-100 text-amber-900 px-2.5 py-0.5 rounded-full border border-amber-300 font-bold">
              Continuous Risk Watchlist
            </span>
          </div>
          <p className="text-xs text-blue-900 max-w-3xl font-medium">
            Instead of reactively analyzing after an oil spill occurs, SagarDrishti continuously monitors vessels inside
            environmentally sensitive marine sanctuaries. Suspicious maneuvers (unexpected stops, sharp heading turns, AIS signal dark gaps) trigger immediate alerts.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-blue-50 border border-blue-300 text-blue-950 text-xs font-bold transition-all disabled:opacity-50 shadow-xs"
        >
          <RefreshCw className={`w-4 h-4 text-blue-600 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Watchlist</span>
        </button>
      </div>

      {/* Sensitive Zones Cards Row */}
      <div>
        <h3 className="text-sm font-bold text-blue-950 font-heading mb-3 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-blue-600" />
          Protected Eco-Sensitive Marine Reserves
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sensitiveZones.map((zone) => (
            <div
              key={zone.id || zone.name}
              className="glass-panel p-4 rounded-2xl border border-blue-200/90 bg-gradient-to-br from-white via-blue-50/60 to-sky-100/60 shadow-xs hover:border-blue-400 hover:shadow-md transition-all text-center space-y-1.5"
            >
              <div className="text-xs font-bold text-blue-950 font-heading truncate">{zone.name}</div>
              <div className="text-[11px] text-blue-800/80 font-mono font-medium">
                ({zone.lat.toFixed(2)}°N, {zone.lon.toFixed(2)}°E)
              </div>
              <div className="text-[10px] text-blue-950 font-bold inline-block px-2.5 py-0.5 rounded-md bg-blue-100 border border-blue-300">
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
            <h3 className="text-sm font-bold text-blue-950 font-heading flex items-center gap-2">
              <Compass className="w-4 h-4 text-blue-600" />
              Sanctuary Surveillance Map
            </h3>
            <span className="text-[11px] text-blue-900/80 font-medium">Live Vessel Positions</span>
          </div>

          <div className="relative w-full h-[480px] rounded-2xl overflow-hidden border border-blue-200 glass-panel shadow-sm">
            <MapContainer
              center={[14.5, 72.5]}
              zoom={6}
              scrollWheelZoom={true}
              className="w-full h-full"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Render Sanctuary Circles */}
              {sensitiveZones.map((zone) => (
                <Circle
                  key={zone.name}
                  center={[zone.lat, zone.lon]}
                  radius={zone.radius_km * 1000}
                  pathOptions={{
                    color: '#2563eb',
                    weight: 2,
                    dashArray: '4, 4',
                    fillColor: '#2563eb',
                    fillOpacity: 0.15,
                  }}
                >
                  <Popup>
                    <div className="p-1 font-sans">
                      <div className="font-bold text-blue-950 text-xs">{zone.name}</div>
                      <div className="text-[11px] text-blue-800 font-medium">Protected Marine Reserve</div>
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
                        <div className="font-bold text-blue-950 text-xs font-mono">MMSI: {item.mmsi}</div>
                        <div className="text-[11px] text-blue-800 font-semibold mt-0.5">
                          Zone: {item.zone}
                        </div>
                        <div className="text-[11px] text-amber-800 font-medium mt-0.5">
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
          <div className="glass-panel p-4 rounded-2xl border border-blue-200/90 bg-white/95 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-blue-200/80 pb-3">
              <h3 className="text-sm font-bold text-blue-950 font-heading flex items-center gap-2">
                <Radio className="w-4 h-4 text-rose-600 animate-pulse" />
                Active Vessel Surveillance Alerts
              </h3>
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-md bg-blue-100 text-blue-950 border border-blue-300">
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
                    className={`glass-panel rounded-2xl p-4 border transition-all ${isCritical
                        ? 'border-rose-300 bg-rose-50/70 shadow-xs'
                        : 'border-blue-200 bg-gradient-to-br from-white to-blue-50/60'
                      }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-blue-950 font-mono">MMSI: {item.mmsi}</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${isCritical
                              ? 'bg-rose-100 text-rose-800 border border-rose-300'
                              : 'bg-blue-100 text-blue-900 border border-blue-300'
                            }`}
                        >
                          {isCritical ? 'CRITICAL ALERT' : 'NORMAL TRANSIT'}
                        </span>
                      </div>

                      <div className={`text-base font-extrabold font-heading ${isCritical ? 'text-rose-700' : 'text-blue-700'}`}>
                        {score.toFixed(0)} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                      </div>
                    </div>

                    <div className="text-xs text-blue-900/80 mt-1">
                      Zone: <b className="text-blue-950">{item.zone}</b> | Type: <b className="text-slate-800">{item.vessel_type || 'Tanker'}</b>
                    </div>

                    {/* Evidence Bullets */}
                    <div className="mt-3 pt-2.5 border-t border-blue-100 space-y-1">
                      {item.evidence && item.evidence.length > 0 ? (
                        item.evidence.map((ev, idx) => (
                          <div key={idx} className="text-xs text-rose-900 flex items-start gap-1.5 font-medium">
                            <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
                            <span>{ev}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-emerald-800 flex items-center gap-1.5 font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
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
