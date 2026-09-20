import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Droplet, ShieldAlert, AlertCircle, ArrowRight, Activity, Clock, Scan, Satellite } from 'lucide-react';

export default function OverviewTab({ categoriesData, proactiveData, onSelectSpill, onSelectVessel }) {
  const [satellitePasses] = useState(26);
  const oilSpills = (categoriesData?.categories?.['Oil'] || []).slice(0, 3);
  const watchlist = proactiveData?.watchlist || [];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 relative">


      {/* Top Banner Control */}
      <div className="relative overflow-hidden glass-panel p-6 rounded-2xl border border-blue-300/80 bg-gradient-to-r from-blue-100/90 via-sky-50/90 to-indigo-100/80 shadow-md">
        <div className="flex items-center justify-between relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="relative p-2 bg-blue-600 rounded-xl shadow-inner border border-blue-500 overflow-hidden">
              <LayoutDashboard className="w-6 h-6 text-white relative z-10" />
              <div className="absolute inset-0 bg-sky-300/30 w-full h-full animate-[spin_3s_linear_infinite] origin-bottom-right" style={{ clipPath: 'polygon(50% 50%, 100% 0, 100% 100%)' }}></div>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-blue-950 font-heading">
                Command Center Overview
              </h2>
              <p className="text-sm text-blue-900/80 font-medium mt-1">
                Live status of satellite detections and active maritime surveillance zones.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-end sm:items-center gap-3">
            <div className="flex items-center gap-2 text-blue-800/80 bg-white/50 px-3 py-1.5 rounded-lg border border-blue-200/50 shadow-sm backdrop-blur-sm">
              <Satellite className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-semibold">
                Satellite passes checked: <span className="font-mono font-bold text-blue-900">{satellitePasses}</span>
              </span>
            </div>

            <div className="hidden sm:flex items-center gap-2 text-sky-600/60 bg-white/40 px-3 py-1.5 rounded-lg border border-sky-200/50">
              <Scan className="w-4 h-4 animate-pulse" />
              <span className="text-xs font-bold font-mono tracking-widest">SCANNING</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Spills Panel */}
        <div className="glass-panel p-5 rounded-2xl border border-blue-200/90 bg-white/95 shadow-md flex flex-col h-[500px]">
          <div className="flex items-center justify-between border-b border-blue-200/80 pb-4 mb-4">
            <h3 className="text-base font-bold text-blue-950 font-heading flex items-center gap-2">
              <Droplet className="w-5 h-5 text-sky-500" />
              Detected Oil Spills
            </h3>
            <span className="text-xs font-bold px-2.5 py-1 rounded-md bg-sky-100 text-sky-900 border border-sky-300">
              {oilSpills.length} Active Detections
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {oilSpills.length > 0 ? (
              oilSpills.map((spill, idx) => {
                const imagePath = `data/raw/SARSatelite/Images/Oil/${spill}`;
                return (
                  <div
                    key={idx}
                    onClick={() => onSelectSpill(imagePath)}
                    className="group cursor-pointer glass-panel rounded-xl p-4 border border-blue-200 bg-gradient-to-br from-white to-sky-50/50 hover:border-sky-400 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-bold text-sm text-blue-950 font-mono mb-1">{spill}</div>
                        <div className="text-xs text-blue-800 flex items-center gap-1">
                          <Activity className="w-3.5 h-3.5 text-sky-500" />
                          <span>Awaiting full forensic analysis</span>
                        </div>
                      </div>
                      <div className="p-1.5 rounded-full bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                        <ArrowRight className="w-4 h-4" />
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center text-blue-900/70 space-y-2">
                <div className="p-3 bg-emerald-100 rounded-full border border-emerald-200">
                  <Activity className="w-6 h-6 text-emerald-600" />
                </div>
                <p className="font-bold">No Active Spills</p>
                <p className="text-xs">All monitored zones are currently clear.</p>
              </div>
            )}
          </div>
        </div>

        {/* Proactive Watchlist Panel */}
        <div className="glass-panel p-5 rounded-2xl border border-blue-200/90 bg-white/95 shadow-md flex flex-col h-[500px]">
          <div className="flex items-center justify-between border-b border-blue-200/80 pb-4 mb-4">
            <h3 className="text-base font-bold text-blue-950 font-heading flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-500" />
              Proactive Watchlist
            </h3>
            <span className="text-xs font-bold px-2.5 py-1 rounded-md bg-amber-100 text-amber-900 border border-amber-300">
              {watchlist.length} Flagged Vessels
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {watchlist.length > 0 ? (
              watchlist.map((vessel) => {
                const isCritical = vessel.risk_score >= 50;
                return (
                  <div
                    key={vessel.mmsi}
                    onClick={() => onSelectVessel(vessel.mmsi)}
                    className={`group cursor-pointer glass-panel rounded-xl p-4 border transition-all ${isCritical
                        ? 'border-rose-300 bg-rose-50/70 hover:border-rose-400 hover:shadow-md'
                        : 'border-blue-200 bg-gradient-to-br from-white to-blue-50/60 hover:border-blue-400 hover:shadow-md'
                      }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-sm text-blue-950 font-mono">MMSI: {vessel.mmsi}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${isCritical ? 'bg-rose-100 text-rose-800' : 'bg-blue-100 text-blue-900'
                            }`}>
                            {isCritical ? 'CRITICAL ALERT' : 'WATCHING'}
                          </span>
                        </div>
                        <div className="text-xs text-blue-900/80 flex items-center gap-1.5 mt-1">
                          <AlertCircle className={`w-3.5 h-3.5 ${isCritical ? 'text-rose-500' : 'text-amber-500'}`} />
                          <span>Zone: {vessel.zone}</span>
                        </div>
                        <div className="text-xs text-blue-900/80 flex items-center gap-1.5 mt-1">
                          <Clock className="w-3.5 h-3.5 text-blue-500" />
                          <span className="font-mono">Score: {vessel.risk_score.toFixed(0)}/100</span>
                        </div>
                      </div>
                      <div className={`p-1.5 rounded-full transition-colors ${isCritical
                          ? 'bg-rose-100 text-rose-600 group-hover:bg-rose-600 group-hover:text-white'
                          : 'bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white'
                        }`}>
                        <ArrowRight className="w-4 h-4" />
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center text-blue-900/70 space-y-2">
                <div className="p-3 bg-emerald-100 rounded-full border border-emerald-200">
                  <ShieldAlert className="w-6 h-6 text-emerald-600" />
                </div>
                <p className="font-bold">No Vessel Alerts</p>
                <p className="text-xs">No suspicious maneuvers detected in sensitive zones.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
