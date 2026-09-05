import React, { useState } from 'react';
import { Ship, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, Clock, MapPin, Compass } from 'lucide-react';

export default function VesselCard({ vessel, rank, isSelected, onSelect }) {
  const [expanded, setExpanded] = useState(false);
  const score = vessel.attribution_score;
  const isHigh = score >= 70;
  const isMedium = score >= 40;

  const statusColor = isHigh
    ? { border: 'border-rose-500/50', bg: 'bg-rose-500/10', text: 'text-rose-400', badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40' }
    : isMedium
    ? { border: 'border-amber-500/50', bg: 'bg-amber-500/10', text: 'text-amber-400', badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40' }
    : { border: 'border-teal-500/40', bg: 'bg-teal-500/10', text: 'text-teal-400', badge: 'bg-teal-500/20 text-teal-300 border-teal-500/40' };

  return (
    <div
      onClick={onSelect}
      className={`glass-panel-interactive rounded-xl p-4 transition-all cursor-pointer ${
        isSelected ? 'glass-card-selected border-teal-500/60 ring-1 ring-teal-500/40' : ''
      }`}
    >
      {/* Top Main Row */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs font-heading ${statusColor.bg} ${statusColor.text}`}>
            #{rank}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white font-mono">MMSI: {vessel.mmsi}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${statusColor.badge}`}>
                {vessel.confidence_level} Confidence
              </span>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
              <span>{vessel.vessel_type}</span>
              <span>•</span>
              <span className="flex items-center gap-1 text-slate-300">
                <MapPin className="w-3 h-3 text-teal-400" />
                {vessel.closest_distance_km} km to origin
              </span>
            </div>
          </div>
        </div>

        {/* Attribution Score Badge */}
        <div className="text-right">
          <div className={`text-xl font-bold font-heading ${statusColor.text}`}>
            {score.toFixed(1)} <span className="text-xs text-slate-400 font-normal">/ 100</span>
          </div>
          <div className="text-[10px] text-slate-400">Attribution Score</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-900 h-2 rounded-full mt-3 overflow-hidden border border-slate-800">
        <div
          className={`h-full transition-all duration-700 ${
            isHigh ? 'bg-gradient-to-r from-amber-500 to-rose-500' : isMedium ? 'bg-gradient-to-r from-teal-500 to-amber-500' : 'bg-gradient-to-r from-teal-500 to-cyan-400'
          }`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>

      {/* Expandable Evidence Breakdown */}
      <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between">
        <span className="text-xs text-slate-400 flex items-center gap-1">
          <Clock className="w-3.5 h-3.5 text-teal-400" />
          Time Offset: <b className="text-slate-200">{vessel.time_delta_hours} hrs</b>
        </span>

        <button
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="text-xs text-teal-400 hover:text-teal-300 flex items-center gap-1 font-medium"
        >
          <span>{expanded ? 'Hide Evidence' : 'View Evidence'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="mt-3 p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-xs space-y-1.5 animate-fadeIn">
          <div className="font-semibold text-slate-300 border-b border-slate-800 pb-1 mb-1 font-heading">
            🔍 Attribution Evidence Bullets:
          </div>
          {vessel.evidence && vessel.evidence.length > 0 ? (
            vessel.evidence.map((ev, idx) => (
              <div key={idx} className="flex items-start gap-2 text-slate-300">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                <span>{ev}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Normal vessel transit with low attribution correlation.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
