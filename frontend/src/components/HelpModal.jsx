import React from 'react';
import { X, Radar, Compass, ShieldCheck, Waves, Info, HelpCircle } from 'lucide-react';

export default function HelpModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4 bg-blue-950/50 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-3xl rounded-3xl border border-blue-300 bg-white/95 p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-blue-200/80 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-blue-100/90 text-blue-800 border border-blue-300">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-blue-950 font-heading">
                SagarDrishti System Guide & Concepts
              </h2>
              <p className="text-xs text-blue-900/80 font-medium">
                Self-Explanatory Overview of Marine Oil Spill Attribution Mechanics
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-blue-100/80 hover:bg-blue-200 text-blue-950 transition-colors border border-blue-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Card 1: SAR Radar Physics */}
          <div className="p-4 bg-gradient-to-br from-blue-50/90 to-sky-100/80 rounded-2xl border border-blue-200 space-y-2">
            <div className="flex items-center gap-2 text-blue-950 font-extrabold font-heading text-sm">
              <Radar className="w-4 h-4 text-blue-600" />
              1. Satellite SAR Radar Detection
            </div>
            <p className="text-blue-950/90 leading-relaxed font-medium">
              Sentinel-1 Synthetic Aperture Radar (SAR) transmits microwave pulses to the ocean surface. Oil slicks damp short capillary ocean waves, creating a smooth surface that reflects radar energy away from the satellite, appearing as <b className="text-blue-950">dark low-backscatter regions</b> regardless of cloud cover or night.
            </p>
          </div>

          {/* Card 2: Backward Drift Hindcast */}
          <div className="p-4 bg-gradient-to-br from-blue-50/90 to-sky-100/80 rounded-2xl border border-blue-200 space-y-2">
            <div className="flex items-center gap-2 text-blue-950 font-extrabold font-heading text-sm">
              <Compass className="w-4 h-4 text-blue-600" />
              2. Backward Particle Drift Hindcast
            </div>
            <p className="text-blue-950/90 leading-relaxed font-medium">
              Using ocean current velocity (<span className="font-mono text-blue-900 font-bold">v_current</span>) and surface wind leeway (<span className="font-mono text-blue-900 font-bold">3% v_wind</span>), SagarDrishti initializes hundreds of particles on the detected slick boundary and advects them backwards in time to compute the <b className="text-blue-950">estimated release origin centroid</b> and release time window.
            </p>
          </div>

          {/* Card 3: AIS Attribution Scoring */}
          <div className="p-4 bg-gradient-to-br from-blue-50/90 to-sky-100/80 rounded-2xl border border-blue-200 space-y-2">
            <div className="flex items-center gap-2 text-amber-950 font-extrabold font-heading text-sm">
              <ShieldCheck className="w-4 h-4 text-amber-600" />
              3. AIS Multi-Factor Attribution
            </div>
            <p className="text-blue-950/90 leading-relaxed font-medium">
              Candidate vessels within radius <span className="font-mono text-amber-900 font-bold">R=50km</span> of the origin window are evaluated across 6 parameters: Spatial proximity, Temporal offset, Trajectory intersection, Speed anomalies (mid-route stops), Sharp heading turns, and AIS signal dark gaps.
            </p>
          </div>

          {/* Card 4: Proactive Surveillance */}
          <div className="p-4 bg-gradient-to-br from-blue-50/90 to-sky-100/80 rounded-2xl border border-blue-200 space-y-2">
            <div className="flex items-center gap-2 text-rose-950 font-extrabold font-heading text-sm">
              <Waves className="w-4 h-4 text-rose-600" />
              4. Proactive Sanctuary Surveillance
            </div>
            <p className="text-blue-950/90 leading-relaxed font-medium">
              Instead of waiting for a disaster, SagarDrishti actively monitors protected marine reserves (such as Laccadive & Malvan Sanctuaries) to flag illegal dumping or illegal anchoring before slicks expand.
            </p>
          </div>
        </div>

        {/* Footer Button */}
        <div className="flex justify-end pt-2 border-t border-blue-200/80">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-700 via-indigo-600 to-blue-800 hover:from-blue-600 hover:to-indigo-500 text-white font-bold text-xs transition-all shadow-md shadow-blue-700/25 border border-blue-400/40"
          >
            Got it, Let's Explore!
          </button>
        </div>
      </div>
    </div>
  );
}
