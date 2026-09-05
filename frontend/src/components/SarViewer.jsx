import React, { useState, useEffect } from 'react';
import { Eye, Layers, Image as ImageIcon, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

export default function SarViewer({ currentImagePath, previewData, onSelectImage, categoriesData, loading }) {
  const [selectedCategory, setSelectedCategory] = useState('Oil');
  const [selectedFile, setSelectedFile] = useState('');

  useEffect(() => {
    if (categoriesData?.categories?.[selectedCategory]?.length > 0) {
      const firstFile = categoriesData.categories[selectedCategory][0];
      setSelectedFile(firstFile);
    }
  }, [selectedCategory, categoriesData]);

  const handleApplyDatasetImage = () => {
    if (selectedCategory && selectedFile) {
      const fullRelPath = `data/raw/SARSatelite/Images/${selectedCategory}/${selectedFile}`;
      onSelectImage(fullRelPath);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
      {/* Header & Dataset Launcher Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-2.5">
          <Layers className="w-5 h-5 text-teal-400" />
          <h3 className="text-base font-semibold text-white font-heading">
            Sentinel-1 SAR Radar Imagery & Segmentation Preview
          </h3>
        </div>

        {/* Category & File Picker */}
        {categoriesData?.has_real_dataset && (
          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-teal-500"
            >
              {Object.keys(categoriesData.categories || {}).map((cat) => (
                <option key={cat} value={cat}>
                  Category: {cat} ({categoriesData.categories[cat]?.length || 0})
                </option>
              ))}
            </select>

            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-teal-500 max-w-[180px] truncate"
            >
              {(categoriesData.categories[selectedCategory] || []).map((file) => (
                <option key={file} value={file}>
                  {file}
                </option>
              ))}
            </select>

            <button
              onClick={handleApplyDatasetImage}
              disabled={loading}
              className="flex items-center gap-1 bg-teal-600 hover:bg-teal-500 text-white text-xs px-3 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
              <span>Load SAR</span>
            </button>
          </div>
        )}
      </div>

      {/* Side-by-Side Image Container */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Box 1: SAR VV Band */}
        <div className="flex flex-col gap-2 bg-slate-950/70 p-3 rounded-xl border border-slate-800/90">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-mono text-teal-300 font-medium">Radar VV Backscatter Band</span>
            <span className="text-[11px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">C-Band SAR</span>
          </div>

          <div className="relative aspect-square rounded-lg overflow-hidden bg-slate-900 border border-slate-800 flex items-center justify-center group">
            {previewData?.sar_image_base64 ? (
              <img
                src={previewData.sar_image_base64}
                alt="SAR VV Band"
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 text-slate-500 text-xs p-6 text-center">
                <ImageIcon className="w-8 h-8 stroke-1 text-slate-600" />
                <span>Synthetic Radar Simulation Active</span>
              </div>
            )}

            <div className="absolute bottom-2 left-2 bg-slate-950/80 backdrop-blur px-2 py-1 rounded text-[10px] text-slate-300 border border-slate-800">
              Low Backscatter = Dark Spot
            </div>
          </div>
        </div>

        {/* Box 2: Ground Truth / U-Net Segmentation Mask */}
        <div className="flex flex-col gap-2 bg-slate-950/70 p-3 rounded-xl border border-slate-800/90">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-mono text-cyan-300 font-medium">Spill Segmentation Mask</span>
            <span className="text-[11px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">Binary Mask</span>
          </div>

          <div className="relative aspect-square rounded-lg overflow-hidden bg-slate-900 border border-slate-800 flex items-center justify-center group">
            {previewData?.mask_image_base64 ? (
              <img
                src={previewData.mask_image_base64}
                alt="Segmentation Mask"
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 filter hue-rotate-180 brightness-110"
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-center p-6 gap-2 text-slate-500 text-xs">
                <Layers className="w-8 h-8 stroke-1 text-slate-600" />
                <span>Segmentation Mask Available for Real SAR Dataset</span>
              </div>
            )}

            <div className="absolute bottom-2 right-2 bg-slate-950/80 backdrop-blur px-2 py-1 rounded text-[10px] text-teal-300 border border-teal-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-teal-400" />
              <span>Edge Detection Verified</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
