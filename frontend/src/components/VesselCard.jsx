import React, { useState } from 'react';
import { Ship, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, Clock, MapPin, Compass } from 'lucide-react';

export default function VesselCard({ vessel, rank, isSelected, onSelect }) {
  const [expanded, setExpanded] = useState(false);
  const score = vessel.attribution_score;
  const isHigh = score >= 70;
  const isMedium = score >= 40;

  const statusColor = isHigh
    ? { border: 'border-rose-300', bg: 'bg-rose-100 text-rose-800', text: 'text-rose-700', badge: 'bg-rose-100 text-rose-800 border-rose-300' }
    : isMedium
    ? { border: 'border-amber-300', bg: 'bg-amber-100 text-amber-800', text: 'text-amber-700', badge: 'bg-amber-100 text-amber-800 border-amber-300' }
    : { border: 'border-blue-300', bg: 'bg-blue-100 text-blue-800', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-800 border-blue-300' };

  return (
    <div
      onClick={onSelect}
      className={`glass-panel-interactive rounded-2xl p-4 transition-all cursor-pointer bg-white/95 border border-blue-200/90 shadow-md ${
        isSelected ? 'glass-card-selected border-blue-600 ring-2 ring-blue-600/30' : ''
      }`}
    >
      {/* Top Main Row */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs font-heading ${statusColor.bg}`}>
            #{rank}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-blue-950 font-mono">MMSI: {vessel.mmsi}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${statusColor.badge}`}>
                {vessel.confidence_level} Confidence
              </span>
            </div>
            <div className="text-xs text-blue-900/80 flex items-center gap-2 mt-0.5 font-medium">
              <span>{vessel.vessel_type}</span>
              <span>•</span>
              <span className="flex items-center gap-1 text-blue-950 font-medium">
                <MapPin className="w-3 h-3 text-blue-600" />
                {vessel.closest_distance_km} km to origin
              </span>
            </div>
          </div>
        </div>

        {/* Attribution Score Badge */}
        <div className="text-right">
          <div className={`text-xl font-extrabold font-heading ${statusColor.text}`}>
            {score.toFixed(1)} <span className="text-xs text-slate-400 font-normal">/ 100</span>
          </div>
          <div className="text-[10px] text-blue-900/80 font-bold uppercase tracking-wider">Attribution</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-blue-100/90 h-2.5 rounded-full mt-3 overflow-hidden border border-blue-200">
        <div
          className={`h-full transition-all duration-700 ${
            isHigh ? 'bg-gradient-to-r from-amber-500 via-rose-500 to-rose-600' : isMedium ? 'bg-gradient-to-r from-blue-600 via-sky-500 to-amber-500' : 'bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600'
          }`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>

      {/* Expandable Evidence Breakdown */}
      <div className="mt-3 pt-2.5 border-t border-blue-100 flex items-center justify-between">
        <span className="text-xs text-blue-900/80 flex items-center gap-1 font-medium">
          <Clock className="w-3.5 h-3.5 text-blue-600" />
          Time Offset: <b className="text-blue-950 font-mono">{vessel.time_delta_hours} hrs</b>
        </span>

        <button
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="text-xs text-blue-700 hover:text-blue-950 flex items-center gap-1 font-bold"
        >
          <span>{expanded ? 'Hide Evidence' : 'View Evidence'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="mt-3 p-3.5 bg-blue-100/70 rounded-xl border border-blue-300 text-xs space-y-1.5 animate-fadeIn">
          <div className="font-bold text-blue-950 border-b border-blue-300/80 pb-1 mb-1 font-heading">
            🔍 Attribution Evidence Bullets:
          </div>
          {vessel.evidence && vessel.evidence.length > 0 ? (
            vessel.evidence.map((ev, idx) => (
              <div key={idx} className="flex items-start gap-2 text-slate-800 font-medium">
                <AlertCircle className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                <span>{ev}</span>
              </div>
            ))
          ) : (
            <div className="text-emerald-800 flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Normal vessel transit with low attribution correlation.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
