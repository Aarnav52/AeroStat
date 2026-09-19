import React from 'react';
import {
  Plane,
  Map,
  BarChart3,
  Layers,
  Clock,
  Calculator,
  Database,
  FileText,
  Activity,
  BookOpen
} from 'lucide-react';

export default function Sidebar({ activeView, setActiveView }) {
  const navItems = [
    { id: 'map', label: 'Airfare Intelligence', icon: Map, badge: 'LIVE' },
    { id: 'macro', label: 'Route Analytics', icon: BarChart3 },
    { id: 'airlines', label: 'Airline Analytics', icon: Plane },
    { id: 'telemetry', label: 'Governance & Telemetry', icon: Activity },
    { id: 'live', label: 'Live Scraper', icon: Database, badge: 'LIVE' },
    { id: 'methodology', label: 'Methodology', icon: FileText, badge: 'NEW' },
  ];

  const handleNavClick = (id) => {
    setActiveView(id);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <aside className="w-16 lg:w-60 glass-strong flex flex-col justify-between fixed top-0 left-0 bottom-0 z-50 transition-all duration-300">
      {/* Top Brand Header */}
      <div>
        <div
          onClick={() => handleNavClick('landing')}
          className="p-4 lg:px-5 lg:py-4 flex items-center space-x-3 border-b border-slate-800/50 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl glass-soft flex items-center justify-center text-white font-bold shrink-0 transform transition group-hover:scale-105">
            <Plane className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div className="hidden lg:block overflow-hidden">
            <div className="flex items-center space-x-2">
              <span className="text-lg font-extrabold tracking-tight text-white font-sans">AeroStat</span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium truncate">Real-Time Airfare Intelligence</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-2 lg:p-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all relative group cursor-pointer ${isActive
                    ? 'glass-tab-active'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`}
                title={item.label}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
                <span className="hidden lg:inline truncate">{item.label}</span>

                {item.badge && (
                  <span className={`hidden lg:inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold ml-auto font-mono ${item.badge === 'LIVE'
                      ? 'glass-soft text-sky-300'
                      : 'glass-soft text-emerald-300'
                    }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom System Status & Navigation */}
      <div className="p-4 border-t border-slate-800/50 bg-transparent flex flex-col space-y-3">
        <button
          onClick={() => handleNavClick('landing')}
          className="hidden lg:flex items-center justify-center space-x-2 w-full px-3 py-2 rounded-xl bg-slate-900/40 hover:bg-slate-800/60 border border-slate-700/50 text-slate-300 text-xs font-semibold transition-all cursor-pointer shadow-sm group backdrop-blur-md"
        >
          <span className="group-hover:-translate-x-1 transition-transform">←</span>
          <span>Return to Landing</span>
        </button>

        <div className="hidden lg:flex items-center justify-between px-1">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-semibold text-slate-300 font-mono text-[11px]">System Live</span>
          </div>
          <div className="text-[9px] text-slate-500 font-mono text-right leading-tight">
            <div>v2.4 (IST)</div>
            <div>MoSPI / DGCA</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
