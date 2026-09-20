import React from 'react';
import { Waves, Radar, ShieldAlert, FlaskConical, HelpCircle, Activity, LayoutDashboard } from 'lucide-react';
import logo from '../../public/logo.png';

export default function Header({ activeTab, setActiveTab, backendStatus, onOpenHelp }) {
  return (
    <header className="sticky top-0 z-50 bg-gradient-to-r from-blue-950 via-slate-900 to-blue-950 text-white border-b border-blue-800/80 px-4 lg:px-8 py-3.5 mb-6 shadow-xl shadow-blue-950/20 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand Header */}
        <div className="flex items-center gap-3.5">
          <div className="flex items-center justify-center w-12 h-12 relative">
            <img src={logo} alt="SagarDrishti Logo" className="absolute w-[300%] h-[300%] max-w-none object-contain pointer-events-none" style={{ left: '-140%', top: '-100%' }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-heading flex items-center gap-2">
                SagarDrishti <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-800/80 text-sky-200 border border-blue-600/80 font-sans font-bold">सागरदृष्टि</span>
              </h1>
            </div>
            <p className="text-xs text-blue-200/90 font-sans font-medium">
              Automated Satellite Oil Spill Detection & AIS Vessel Attribution System
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 bg-blue-900/60 p-1.5 rounded-2xl border border-blue-700/60 shadow-inner overflow-x-auto">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all whitespace-nowrap ${activeTab === 'overview'
              ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/25 border border-sky-400/40'
              : 'text-blue-200 hover:text-white hover:bg-blue-800/50'
              }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Live Monitor</span>
          </button>

          <button
            onClick={() => setActiveTab('forensic')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${activeTab === 'forensic'
              ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/25 border border-sky-400/40'
              : 'text-blue-200 hover:text-white hover:bg-blue-800/50'
              }`}
          >
            <Radar className="w-4 h-4" />
            <span>Forensic Analysis</span>
          </button>

          <button
            onClick={() => setActiveTab('proactive')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all relative ${activeTab === 'proactive'
              ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/25 border border-sky-400/40'
              : 'text-blue-200 hover:text-white hover:bg-blue-800/50'
              }`}
          >
            <ShieldAlert className={`w-4 h-4 ${activeTab === 'proactive' ? 'text-amber-300' : 'text-amber-400'}`} />
            <span>Proactive Surveillance</span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400"></span>
            </span>
          </button>

          <button
            onClick={() => setActiveTab('sandbox')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${activeTab === 'sandbox'
              ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/25 border border-sky-400/40'
              : 'text-blue-200 hover:text-white hover:bg-blue-800/50'
              }`}
          >
            <FlaskConical className="w-4 h-4" />
            <span>Drift Sandbox</span>
          </button>
        </div>

        {/* Right Status Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-blue-900/80 border border-blue-700/80 text-xs shadow-xs">
            <span className="flex h-2 w-2 relative">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${backendStatus === 'connected' ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${backendStatus === 'connected' ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
            </span>
            <span className="text-blue-200 font-medium hidden sm:inline ml-1">Monitoring:</span>
            <span className={backendStatus === 'connected' ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
              {backendStatus === 'connected' ? 'Active' : 'Connecting...'}
            </span>
          </div>

          <button
            onClick={onOpenHelp}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white border border-sky-400/50 text-xs transition-all font-semibold shadow-md shadow-sky-500/20"
            title="Open Interactive Guide & Concept Explainer"
          >
            <HelpCircle className="w-4 h-4 text-sky-100" />
            <span className="hidden sm:inline">How It Works</span>
          </button>
        </div>
      </div>
    </header>
  );
}
