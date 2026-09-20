import React from 'react';

export default function MetricCard({ title, value, subtext, icon: Icon, color = 'blue', badge }) {
  const colorMap = {
    teal: {
      border: 'border-teal-300/80',
      iconBg: 'bg-teal-100/80 text-teal-800 border border-teal-300/70',
      text: 'text-teal-950',
    },
    cyan: {
      border: 'border-cyan-300/80',
      iconBg: 'bg-cyan-100/80 text-cyan-800 border border-cyan-300/70',
      text: 'text-cyan-950',
    },
    blue: {
      border: 'border-blue-300/80',
      iconBg: 'bg-blue-100/90 text-blue-800 border border-blue-300/70',
      text: 'text-blue-950',
    },
    indigo: {
      border: 'border-indigo-300/80',
      iconBg: 'bg-indigo-100/80 text-indigo-800 border border-indigo-300/70',
      text: 'text-indigo-950',
    },
    amber: {
      border: 'border-amber-300/80',
      iconBg: 'bg-amber-100/80 text-amber-800 border border-amber-300/70',
      text: 'text-amber-950',
    },
    rose: {
      border: 'border-rose-300/80',
      iconBg: 'bg-rose-100/80 text-rose-800 border border-rose-300/70',
      text: 'text-rose-950',
    },
  };

  const currentTheme = colorMap[color] || colorMap.blue;

  return (
    <div className={`glass-panel p-3.5 sm:p-4 rounded-2xl border ${currentTheme.border} flex flex-col justify-between gap-2.5 shadow-md relative overflow-hidden group bg-gradient-to-br from-white via-blue-50/60 to-sky-100/60 hover:shadow-lg hover:border-blue-400 transition-all duration-300 min-w-0 w-full`}>
      <div className="flex items-center justify-between gap-1.5 min-w-0">
        <span className="text-[11px] sm:text-xs font-bold text-blue-950 font-heading truncate leading-tight">{title}</span>
        {Icon && (
          <div className={`p-1.5 rounded-xl ${currentTheme.iconBg} shadow-2xs shrink-0`}>
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>

      <div className="min-w-0">
        <div className={`text-base sm:text-lg lg:text-xl font-extrabold font-heading tracking-tight ${currentTheme.text} truncate`}>
          {value}
        </div>
        {subtext && <div className="text-[10px] sm:text-[11px] text-blue-900/80 font-medium mt-0.5 truncate">{subtext}</div>}
      </div>

      {badge && (
        <div className="mt-0.5 min-w-0">
          <span className="text-[9px] sm:text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-100/90 border border-blue-300/80 text-blue-950 inline-block truncate max-w-full">
            {badge}
          </span>
        </div>
      )}
    </div>
  );
}
