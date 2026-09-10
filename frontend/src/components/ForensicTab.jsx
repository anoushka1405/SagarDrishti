import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle, Compass, Wind, Clock, ShieldCheck, MapPin, Download, RefreshCw } from 'lucide-react';
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
  onUploadImage,
  currentImagePath,
}) {
  const [selectedVessel, setSelectedVessel] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const defaultResults = {
    spill_detected: true,
    confidence: 88,
    area_km2: 14.25,
    perimeter_km: 18.60,
    age_low: 3.5,
    age_high: 6.0,
    age_confidence: 82,
    centroid: [18.43, 70.82],
    estimated_origin: [18.43, 70.82],
    origin_uncertainty_km: 4.5,
    spill_polygon_coords: [
      [18.445, 70.805],
      [18.448, 70.835],
      [18.425, 70.840],
      [18.412, 70.815],
      [18.430, 70.798]
    ],
    hindcast_track: [
      [18.43, 70.82],
      [18.41, 70.79],
      [18.39, 70.76],
      [18.37, 70.73]
    ],
    forecast_tracks: {
      "1": [[18.435, 70.825], [18.438, 70.828], [18.432, 70.822]],
      "3": [[18.445, 70.835], [18.448, 70.838], [18.442, 70.832]],
      "6": [[18.460, 70.850], [18.463, 70.854], [18.458, 70.848]]
    },
    ranked_vessels: [
      {
        mmsi: "SYN-998822101",
        vessel_type: "Crude Oil Tanker",
        attribution_score: 77.8,
        closest_distance_km: 1.2,
        time_delta_hours: 0.5,
        confidence_level: "High Probability",
        trajectory: [
          [18.35, 70.70, "2026-08-29T18:00:00Z", 12.0, 45.0],
          [18.39, 70.76, "2026-08-29T18:30:00Z", 11.5, 45.0],
          [18.43, 70.82, "2026-08-29T19:00:00Z", 0.5, 135.0],
          [18.48, 70.88, "2026-08-29T20:15:00Z", 4.0, 45.0]
        ],
        evidence: [
          "Crossed within 1.2km of origin centroid during release window",
          "Speed dropped from 12.0 to 0.5 knots during transit",
          "High historical spill risk profile for crude oil carrier"
        ]
      },
      {
        mmsi: "SYN-445566778",
        vessel_type: "Cargo Vessel",
        attribution_score: 52.4,
        closest_distance_km: 3.8,
        time_delta_hours: 1.8,
        confidence_level: "Moderate Probability",
        trajectory: [
          [18.38, 70.65, "2026-08-29T18:00:00Z", 14.5, 30.0],
          [18.42, 70.72, "2026-08-29T18:30:00Z", 14.2, 30.0],
          [18.45, 70.78, "2026-08-29T19:00:00Z", 14.6, 30.0]
        ],
        evidence: [
          "Crossed within 3.8km of origin centroid",
          "Maintained constant 14.2 knots transit speed"
        ]
      },
      {
        mmsi: "SYN-112233445",
        vessel_type: "Container Ship",
        attribution_score: 41.2,
        closest_distance_km: 6.4,
        time_delta_hours: 2.5,
        confidence_level: "Low Probability",
        trajectory: [
          [18.25, 70.80, "2026-08-29T18:00:00Z", 10.0, 60.0],
          [18.30, 70.85, "2026-08-29T18:45:00Z", 0.2, 180.0],
          [18.36, 70.90, "2026-08-29T20:00:00Z", 3.5, 60.0]
        ],
        evidence: ["Passed outside primary 5km uncertainty radius"]
      }
    ]
  };

  const results = pipelineResults || defaultResults;

  const handleExportReport = async () => {
    setDownloading(true);
    try {
      const res = await fetch('/api/export_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_path: currentImagePath || 'data/raw/sentinel1_sample.tif',
          mock_mode: true,
        }),
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'sagardrishti_report.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Control & Mode Selector */}
      <div className="glass-panel p-5 rounded-2xl border border-blue-300/80 bg-gradient-to-r from-blue-100/90 via-sky-50/90 to-indigo-100/80 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-lg font-extrabold text-blue-950 font-heading flex items-center gap-2">
            <span>Forensic Post-Spill Satellite Attribution</span>
            {results.spill_detected && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-300 font-bold shadow-2xs">
                Oil Spill Detected
              </span>
            )}
          </h2>
          <p className="text-xs text-blue-900/90 font-medium">
            Analyze SAR imagery, backtrack particle drift to estimated release origin, and rank candidate vessels.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <button
            onClick={() => onRunAnalysis(currentImagePath, true)}
            disabled={loading}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-blue-50 border border-blue-300/80 text-blue-950 text-xs font-bold transition-all disabled:opacity-50 shadow-xs"
          >
            <Sparkles className="w-4 h-4 text-blue-600" />
            <span>Run Synthetic Mock Demo</span>
          </button>

          <button
            onClick={() => onRunAnalysis(currentImagePath, false)}
            disabled={loading}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-700 via-indigo-600 to-blue-800 hover:from-blue-600 hover:to-indigo-500 text-white font-bold text-xs shadow-md shadow-blue-700/25 transition-all disabled:opacity-50 border border-blue-400/40"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Processing Pipeline...</span>
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Play className="w-4 h-4 fill-current" />
                <span>Analyze Satellite Pass</span>
              </span>
            )}
          </button>

          <button
            onClick={handleExportReport}
            disabled={downloading}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-950 text-xs font-bold transition-all disabled:opacity-50 shadow-xs"
          >
            <Download className="w-4 h-4 text-amber-700" />
            <span>{downloading ? 'Generating PDF...' : 'Export PDF Report'}</span>
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
            onUploadImage={onUploadImage}
            categoriesData={categoriesData}
            loading={loading}
          />

          {/* Interactive GIS Drift Map */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-blue-950 font-heading flex items-center gap-2">
                <Compass className="w-4 h-4 text-blue-700" />
                Interactive Maritime GIS Layer Plot
              </h3>
              <span className="text-[11px] text-blue-900/80 font-medium">
                OpenStreetMap Tiles • Hydrodynamic Drift Layer
              </span>
            </div>

            <GISMap
              pipelineResults={results}
              onSelectVessel={setSelectedVessel}
              selectedVessel={selectedVessel}
            />
          </div>

          {/* Metric Cards Row (Always Visible) */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Spill Surface Area"
              value={`${results.area_km2 || 0} km²`}
              subtext={`Perimeter: ${results.perimeter_km || 0} km`}
              color="rose"
              badge={`Confidence: ${results.confidence || 0}%`}
            />

            <MetricCard
              title="Estimated Release Age"
              value={`${results.age_low || 3} - ${results.age_high || 6} hrs`}
              subtext={`Confidence: ${results.age_confidence || 82}%`}
              color="amber"
              badge="Backward Advection"
            />

            <MetricCard
              title="Origin Centroid"
              value={
                results.estimated_origin
                  ? `${results.estimated_origin[0].toFixed(2)}N, ${results.estimated_origin[1].toFixed(2)}E`
                  : 'N/A'
              }
              subtext={`Uncertainty: ±${results.origin_uncertainty_km || 4.5} km`}
              color="blue"
              badge="Geodesic Center"
            />

            <MetricCard
              title="Candidates Evaluated"
              value={`${results.ranked_vessels?.length || 0} Vessels`}
              subtext="Radius R=50km"
              color="indigo"
              badge="AIS Spatio-Temporal"
            />
          </div>
        </div>

        {/* Right Column (4 cols): Suspect Vessel Rankings */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-4 rounded-2xl border border-blue-300/80 bg-white/95 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-blue-200/80 pb-3">
              <h3 className="text-sm font-bold text-blue-950 font-heading flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-amber-600" />
                Suspect Vessel Rankings
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-100 text-blue-950 border border-blue-300/80">
                Composite Score
              </span>
            </div>

            {loading ? (
              <div className="p-8 text-center text-blue-900/70 text-xs space-y-3">
                <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
                <p className="font-bold text-blue-950 text-sm">Analyzing Satellite Pass & Drift Trajectories...</p>
                <p className="text-[11px] text-blue-800/80 font-medium">Evaluating AIS candidate vessels within R=50km radius</p>
              </div>
            ) : results.ranked_vessels?.length > 0 ? (
              <div className="space-y-3 max-h-[720px] overflow-y-auto pr-1">
                {results.ranked_vessels.map((vessel, idx) => (
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
              <div className="p-8 text-center text-blue-900/70 text-xs space-y-2">
                <AlertCircle className="w-8 h-8 text-blue-400 mx-auto" />
                <p>Run analysis to load candidate vessel rankings around the spill origin.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
