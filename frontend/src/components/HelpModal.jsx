import React from 'react';
import { X, Radar, Compass, ShieldCheck, Waves, Info, HelpCircle } from 'lucide-react';

export default function HelpModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-3xl rounded-2xl border border-slate-700/80 p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-teal-500/20 text-teal-400 border border-teal-500/30">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white font-heading">
                SagarDrishti System Guide & Concepts
              </h2>
              <p className="text-xs text-slate-400">
                Self-Explanatory Overview of Marine Oil Spill Attribution Mechanics
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Card 1: SAR Radar Physics */}
          <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-teal-300 font-bold font-heading text-sm">
              <Radar className="w-4 h-4 text-teal-400" />
              1. Satellite SAR Radar Detection
            </div>
            <p className="text-slate-300 leading-relaxed">
              Sentinel-1 Synthetic Aperture Radar (SAR) transmits microwave pulses to the ocean surface. Oil slicks damp short capillary ocean waves, creating a smooth surface that reflects radar energy away from the satellite, appearing as <b>dark low-backscatter regions</b> regardless of cloud cover or night.
            </p>
          </div>

          {/* Card 2: Backward Drift Hindcast */}
          <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-cyan-300 font-bold font-heading text-sm">
              <Compass className="w-4 h-4 text-cyan-400" />
              2. Backward Particle Drift Hindcast
            </div>
            <p className="text-slate-300 leading-relaxed">
              Using ocean current velocity (<span className="font-mono text-cyan-300">v_current</span>) and surface wind leeway (<span className="font-mono text-cyan-300">3% v_wind</span>), SagarDrishti initializes hundreds of particles on the detected slick boundary and advects them backwards in time to compute the <b>estimated release origin centroid</b> and release time window.
            </p>
          </div>

          {/* Card 3: AIS Attribution Scoring */}
          <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-bold font-heading text-sm">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              3. AIS Multi-Factor Attribution
            </div>
            <p className="text-slate-300 leading-relaxed">
              Candidate vessels within radius <span className="font-mono text-amber-300">R=50km</span> of the origin window are evaluated across 6 parameters: Spatial proximity, Temporal offset, Trajectory intersection, Speed anomalies (mid-route stops), Sharp heading turns, and AIS signal dark gaps.
            </p>
          </div>

          {/* Card 4: Proactive Surveillance */}
          <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-rose-300 font-bold font-heading text-sm">
              <Waves className="w-4 h-4 text-rose-400" />
              4. Proactive Sanctuary Surveillance
            </div>
            <p className="text-slate-300 leading-relaxed">
              Instead of waiting for a disaster, SagarDrishti actively monitors protected marine reserves (such as Laccadive & Malvan Sanctuaries) to flag illegal dumping or illegal anchoring before slicks expand.
            </p>
          </div>
        </div>

        {/* Footer Button */}
        <div className="flex justify-end pt-2 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs transition-colors"
          >
            Got it, Let's Explore!
          </button>
        </div>
      </div>
    </div>
  );
}
