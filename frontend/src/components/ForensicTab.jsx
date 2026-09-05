import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle, Compass, Wind, Clock, ShieldCheck, MapPin, Download } from 'lucide-react';
import SarViewer from './SarViewer';
import GISMap from './GISMap';
import MetricCard from './MetricCard';
import VesselCard from './VesselCard';

export default function ForensicTab({
  pipelineResults,
  previewData,
  categoriesData,
  loading,
  onRunAnalysis,
  onSelectImage,
  currentImagePath,
}) {
  const [selectedVessel, setSelectedVessel] = useState(null);
  const detected = pipelineResults?.spill_detected;

  return (
    <div className="space-y-6">
      {/* Top Banner Control & Mode Selector */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-lg font-bold text-white font-heading flex items-center gap-2">
            <span>Forensic Post-Spill Satellite Attribution</span>
            {detected && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 font-normal">
                Oil Spill Detected
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400">
            Analyze SAR imagery, backtrack particle drift to estimated release origin, and rank candidate vessels.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <button
            onClick={() => onRunAnalysis(currentImagePath, true)}
            disabled={loading}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-teal-300 text-xs font-semibold transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Run Synthetic Mock Demo</span>
          </button>

          <button
            onClick={() => onRunAnalysis(currentImagePath, false)}
            disabled={loading}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-teal-glow transition-all disabled:opacity-50"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>Processing Pipeline...</span>
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Play className="w-4 h-4 fill-current" />
                <span>Analyze Satellite Pass</span>
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Main Grid: Left GIS Map & Imagery vs Right Suspect Rankings */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): SAR Preview & Interactive Map */}
        <div className="lg:col-span-8 space-y-6">
          {/* Side-by-Side Satellite SAR Viewer */}
          <SarViewer
            currentImagePath={currentImagePath}
            previewData={previewData}
            onSelectImage={onSelectImage}
            categoriesData={categoriesData}
            loading={loading}
          />

          {/* Interactive GIS Drift Map */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white font-heading flex items-center gap-2">
                <Compass className="w-4 h-4 text-teal-400" />
                Interactive Maritime GIS Layer Plot
              </h3>
              <span className="text-[11px] text-slate-400">
                Leaflet Dark Tiles • Hydrodynamic Drift Layer
              </span>
            </div>

            <GISMap
              pipelineResults={pipelineResults}
              onSelectVessel={setSelectedVessel}
              selectedVessel={selectedVessel}
            />
          </div>

          {/* Metric Cards Row */}
          {pipelineResults && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                title="Spill Surface Area"
                value={`${pipelineResults.area_km2 || 0} km²`}
                subtext={`Perimeter: ${pipelineResults.perimeter_km || 0} km`}
                color="rose"
                badge={`Detection Confidence: ${pipelineResults.confidence || 0}%`}
              />

              <MetricCard
                title="Estimated Release Age"
                value={`${pipelineResults.age_low || 6} - ${pipelineResults.age_high || 12} hrs`}
                subtext={`Confidence: ${pipelineResults.age_confidence || 75}%`}
                color="amber"
                badge="Backward Advection"
              />

              <MetricCard
                title="Origin Centroid"
                value={
                  pipelineResults.estimated_origin
                    ? `${pipelineResults.estimated_origin[0].toFixed(2)}N, ${pipelineResults.estimated_origin[1].toFixed(2)}E`
                    : 'N/A'
                }
                subtext={`Uncertainty: ±${pipelineResults.origin_uncertainty_km || 5} km`}
                color="teal"
                badge="Geodesic Center"
              />

              <MetricCard
                title="Candidates Evaluated"
                value={`${pipelineResults.ranked_vessels?.length || 0} Vessels`}
                subtext="Spatio-Temporal Radius R=50km"
                color="cyan"
                badge="AIS Spatio-Temporal"
              />
            </div>
          )}
        </div>

        {/* Right Column (4 cols): Suspect Vessel Rankings */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white font-heading flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-amber-400" />
                Suspect Vessel Rankings
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                Composite Score
              </span>
            </div>

            {pipelineResults?.ranked_vessels?.length > 0 ? (
              <div className="space-y-3 max-h-[720px] overflow-y-auto pr-1">
                {pipelineResults.ranked_vessels.map((vessel, idx) => (
                  <VesselCard
                    key={vessel.mmsi}
                    vessel={vessel}
                    rank={idx + 1}
                    isSelected={selectedVessel?.mmsi === vessel.mmsi}
                    onSelect={() => setSelectedVessel(vessel)}
                  />
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs space-y-2">
                <AlertCircle className="w-8 h-8 text-slate-600 mx-auto" />
                <p>Run analysis to load candidate vessel rankings around the spill origin.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
