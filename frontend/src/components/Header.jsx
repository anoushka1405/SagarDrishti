import React from 'react';
import { Waves, Radar, ShieldAlert, FlaskConical, HelpCircle, Activity } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, backendStatus, onOpenHelp }) {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3 mb-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand Header */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br from-teal-500/20 to-cyan-500/20 border border-teal-500/40 shadow-teal-glow">
            <Radar className="w-6 h-6 text-teal-400 animate-spin" style={{ animationDuration: '6s' }} />
            <div className="absolute w-2 h-2 bg-cyan-400 rounded-full animate-ping" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-heading flex items-center gap-1.5">
                SagarDrishti <span className="text-xs px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30 font-sans">सागरदृष्टि</span>
              </h1>
            </div>
            <p className="text-xs text-slate-400 font-sans">
              Automated Satellite Oil Spill Detection & AIS Vessel Attribution System
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('forensic')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'forensic'
                ? 'bg-gradient-to-r from-teal-500/20 to-cyan-500/20 text-teal-300 border border-teal-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <Radar className="w-4 h-4" />
            <span>Forensic Analysis</span>
          </button>

          <button
            onClick={() => setActiveTab('proactive')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all relative ${
              activeTab === 'proactive'
                ? 'bg-gradient-to-r from-teal-500/20 to-cyan-500/20 text-teal-300 border border-teal-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <span>Proactive Surveillance</span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
          </button>

          <button
            onClick={() => setActiveTab('sandbox')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'sandbox'
                ? 'bg-gradient-to-r from-teal-500/20 to-cyan-500/20 text-teal-300 border border-teal-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <FlaskConical className="w-4 h-4 text-cyan-400" />
            <span>Drift Sandbox</span>
          </button>
        </div>

        {/* Right Status Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950/60 border border-slate-800 text-xs">
            <Activity className={`w-3.5 h-3.5 ${backendStatus === 'connected' ? 'text-emerald-400 animate-pulse' : 'text-rose-400'}`} />
            <span className="text-slate-400 hidden sm:inline">Backend API:</span>
            <span className={backendStatus === 'connected' ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
              {backendStatus === 'connected' ? 'FastAPI Online' : 'Connecting...'}
            </span>
          </div>

          <button
            onClick={onOpenHelp}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-xs text-teal-300 transition-colors font-medium"
            title="Open Interactive Guide & Concept Explainer"
          >
            <HelpCircle className="w-4 h-4" />
            <span className="hidden sm:inline">How It Works</span>
          </button>
        </div>
      </div>
    </header>
  );
}
