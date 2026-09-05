import React from 'react';

export default function MetricCard({ title, value, subtext, icon: Icon, color = 'teal', badge }) {
  const colorMap = {
    teal: {
      border: 'border-teal-500/30',
      iconBg: 'bg-teal-500/10 text-teal-400',
      text: 'text-teal-300',
    },
    cyan: {
      border: 'border-cyan-500/30',
      iconBg: 'bg-cyan-500/10 text-cyan-400',
      text: 'text-cyan-300',
    },
    amber: {
      border: 'border-amber-500/30',
      iconBg: 'bg-amber-500/10 text-amber-400',
      text: 'text-amber-300',
    },
    rose: {
      border: 'border-rose-500/30',
      iconBg: 'bg-rose-500/10 text-rose-400',
      text: 'text-rose-300',
    },
  };

  const currentTheme = colorMap[color] || colorMap.teal;

  return (
    <div className={`glass-panel p-4 rounded-xl border ${currentTheme.border} flex flex-col justify-between gap-3 shadow-lg relative overflow-hidden group`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg ${currentTheme.iconBg}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div>
        <div className={`text-2xl font-bold font-heading tracking-tight ${currentTheme.text}`}>
          {value}
        </div>
        {subtext && <div className="text-[11px] text-slate-400 mt-0.5">{subtext}</div>}
      </div>

      {badge && (
        <div className="mt-1">
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
            {badge}
          </span>
        </div>
      )}
    </div>
  );
}
