import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ForensicTab from './components/ForensicTab';
import ProactiveTab from './components/ProactiveTab';
import SandboxTab from './components/SandboxTab';
import HelpModal from './components/HelpModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('forensic');
  const [currentImagePath, setCurrentImagePath] = useState('data/raw/sentinel1_sample.tif');
  const [pipelineResults, setPipelineResults] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [categoriesData, setCategoriesData] = useState(null);
  const [proactiveData, setProactiveData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState('connecting');
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  // Check health and initial datasets on mount
  useEffect(() => {
    fetchHealth();
    fetchCategories();
    fetchProactiveWatchlist();
    // Run initial mock analysis so user sees interactive data immediately
    runAnalysis('data/raw/sentinel1_sample.tif', true);
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        setBackendStatus('connected');
      } else {
        setBackendStatus('error');
      }
    } catch {
      setBackendStatus('error');
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await fetch('/api/dataset/categories');
      if (res.ok) {
        const data = await res.json();
        setCategoriesData(data);
      }
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  const fetchSarPreview = async (imagePath) => {
    try {
      const res = await fetch(`/api/sar_preview?image_path=${encodeURIComponent(imagePath)}`);
      if (res.ok) {
        const data = await res.json();
        setPreviewData(data);
      }
    } catch (err) {
      console.error('Error fetching SAR preview:', err);
    }
  };

  const fetchProactiveWatchlist = async () => {
    try {
      const res = await fetch('/api/proactive_watchlist');
      if (res.ok) {
        const data = await res.json();
        setProactiveData(data);
      }
    } catch (err) {
      console.error('Error fetching proactive watchlist:', err);
    }
  };

  const runAnalysis = async (imagePath, mockMode = false) => {
    setLoading(true);
    setCurrentImagePath(imagePath);
    fetchSarPreview(imagePath);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_path: imagePath,
          mock_mode: mockMode,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setPipelineResults(data);
      } else {
        console.error('Analysis API returned error:', await res.text());
      }
    } catch (err) {
      console.error('Failed executing analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#060a12] text-slate-100 font-sans pb-12">
      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendStatus={backendStatus}
        onOpenHelp={() => setIsHelpOpen(true)}
      />

      {/* Main Page Container */}
      <main className="max-w-7xl mx-auto px-4 lg:px-8 flex-1 w-full">
        {activeTab === 'forensic' && (
          <ForensicTab
            pipelineResults={pipelineResults}
            previewData={previewData}
            categoriesData={categoriesData}
            loading={loading}
            onRunAnalysis={runAnalysis}
            onSelectImage={(path) => runAnalysis(path, false)}
            currentImagePath={currentImagePath}
          />
        )}

        {activeTab === 'proactive' && (
          <ProactiveTab
            proactiveData={proactiveData}
            loading={loading}
            onRefresh={fetchProactiveWatchlist}
          />
        )}

        {activeTab === 'sandbox' && <SandboxTab />}
      </main>

      {/* Interactive Concept Explainer Modal */}
      <HelpModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />
    </div>
  );
}
