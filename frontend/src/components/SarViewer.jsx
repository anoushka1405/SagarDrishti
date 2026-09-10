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
    <div className="glass-panel rounded-2xl p-5 border border-blue-300/80 bg-white/95 shadow-md flex flex-col gap-4">
      {/* Header & Dataset Launcher Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-blue-200/80 pb-4">
        <div className="flex items-center gap-2.5">
          <Layers className="w-5 h-5 text-blue-600" />
          <h3 className="text-base font-extrabold text-blue-950 font-heading">
            Sentinel-1 SAR Radar Imagery & Segmentation Preview
          </h3>
        </div>

        {/* Category & File Picker */}
        {categoriesData?.has_real_dataset && (
          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-blue-100/80 border border-blue-300 text-xs text-blue-950 rounded-xl px-3 py-1.5 focus:outline-none focus:border-blue-600 font-bold"
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
              className="bg-blue-100/80 border border-blue-300 text-xs text-blue-950 rounded-xl px-3 py-1.5 focus:outline-none focus:border-blue-600 max-w-[180px] truncate font-bold"
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
              className="flex items-center gap-1 bg-gradient-to-r from-blue-700 via-indigo-600 to-blue-800 hover:from-blue-600 hover:to-indigo-500 text-white text-xs px-3.5 py-1.5 rounded-xl font-bold transition-all disabled:opacity-50 shadow-md shadow-blue-700/25 border border-blue-400/40"
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
        <div className="flex flex-col gap-2 bg-gradient-to-br from-blue-50/80 to-sky-100/70 p-3 rounded-2xl border border-blue-200">
          <div className="flex items-center justify-between text-xs text-blue-900/80 px-1">
            <span className="font-mono text-blue-950 font-bold">Radar VV Backscatter Band</span>
            <span className="text-[11px] bg-blue-200/80 text-blue-950 px-2 py-0.5 rounded-md font-bold">C-Band SAR</span>
          </div>

          <div className="relative aspect-square rounded-xl overflow-hidden bg-slate-900 border border-blue-200 flex items-center justify-center group shadow-inner">
            {previewData?.sar_image_base64 ? (
              <img
                src={previewData.sar_image_base64}
                alt="SAR VV Band"
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 text-slate-400 text-xs p-6 text-center">
                <ImageIcon className="w-8 h-8 stroke-1 text-slate-500" />
                <span>Synthetic Radar Simulation Active</span>
              </div>
            )}

            <div className="absolute bottom-2.5 left-2.5 bg-white/95 backdrop-blur px-2.5 py-1 rounded-lg text-[10px] text-blue-950 border border-blue-300 font-bold shadow-xs">
              Low Backscatter = Dark Spot
            </div>
          </div>
        </div>

        {/* Box 2: Ground Truth / U-Net Segmentation Mask */}
        <div className="flex flex-col gap-2 bg-gradient-to-br from-blue-50/80 to-sky-100/70 p-3 rounded-2xl border border-blue-200">
          <div className="flex items-center justify-between text-xs text-blue-900/80 px-1">
            <span className="font-mono text-blue-950 font-bold">Spill Segmentation Mask</span>
            <span className="text-[11px] bg-blue-200/80 text-blue-950 px-2 py-0.5 rounded-md font-bold">Binary Mask</span>
          </div>

          <div className="relative aspect-square rounded-xl overflow-hidden bg-slate-900 border border-blue-200 flex items-center justify-center group shadow-inner">
            {previewData?.mask_image_base64 ? (
              <img
                src={previewData.mask_image_base64}
                alt="Segmentation Mask"
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 filter hue-rotate-180 brightness-110"
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-center p-6 gap-2 text-slate-400 text-xs">
                <Layers className="w-8 h-8 stroke-1 text-slate-500" />
                <span>Segmentation Mask Available for Real SAR Dataset</span>
              </div>
            )}

            <div className="absolute bottom-2.5 right-2.5 bg-white/95 backdrop-blur px-2.5 py-1 rounded-lg text-[10px] text-blue-950 border border-blue-300 flex items-center gap-1 font-bold shadow-xs">
              <CheckCircle2 className="w-3 h-3 text-blue-600" />
              <span>Edge Detection Verified</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
