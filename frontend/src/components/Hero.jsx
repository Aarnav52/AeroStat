import React from 'react';
import { TrendingUp, ArrowDownRight, ArrowUpRight, Sparkles, ChevronDown, BookOpen, Layers, Shield } from 'lucide-react';
import { HERO_STATS } from '../data/mockData';

export default function Hero({ onExploreClick, onWhitepaperClick }) {
  return (
    <section className="relative pt-32 pb-20 overflow-hidden text-slate-100 border-b border-white/5" style={{ background: 'transparent' }}>
      
      {/* Background Decorative Mesh — subtle, transparent */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-tr from-sky-500/10 via-blue-500/5 to-transparent blur-[100px] rounded-full opacity-40"></div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        
        {/* Top Tag Pill */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full glass-soft text-sky-400 text-xs font-bold tracking-wide uppercase shadow-sm mb-6 animate-pulse-slow">
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span>India Aviation Economics • MoSPI Calibrated</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.15] max-w-4xl mx-auto font-sans drop-shadow-lg">
          The First Real-Time <br className="hidden sm:inline" />
          <span className="text-sky-400 drop-shadow-[0_0_15px_rgba(56,189,248,0.3)]">Airfare Price Index</span> for India
        </h1>

        {/* Hero Subtitle */}
        <p className="mt-6 text-base sm:text-lg text-slate-300 max-w-3xl mx-auto font-medium leading-relaxed drop-shadow-md">
          Live benchmark tracking <strong className="text-white font-bold">2,500+ real fares</strong> across
          7 domestic routes, 12 airlines, 5 booking windows (T+1, T+7, T+15, T+30, T+45),
          aggregated via <strong className="text-white font-bold">Jevons price relatives</strong> —
          multilateral GEKS aggregation and DGCA traffic-weighting are the next build phase.
        </p>

        {/* 4 Top KPI Metric Cards */}
        <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          {HERO_STATS.map((stat, idx) => (
            <div 
              key={idx} 
              className="glass-elevated p-5 rounded-2xl text-left"
            >
              <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider mb-1">
                {stat.label}
              </span>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-2xl sm:text-3xl font-extrabold text-white font-mono tracking-tight drop-shadow-md">
                  {stat.value}
                </span>
                {stat.change && (
                  <span className={`inline-flex items-center text-[10px] font-bold px-1.5 py-0.5 rounded glass-soft ${
                    stat.status === 'up' 
                      ? 'text-emerald-400' 
                      : 'text-rose-400'
                  }`}>
                    {stat.status === 'up' ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />}
                    {stat.change}
                  </span>
                )}
              </div>
              <span className="text-[11px] font-medium text-slate-500 mt-2 block font-sans">
                {stat.period || stat.subtext}
              </span>
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button 
            onClick={onExploreClick}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-7 py-3.5 rounded-xl glass-elevated hover:bg-white/10 text-white font-bold text-sm shadow-xl transition-all"
          >
            <span>Explore Live Index</span>
            <ChevronDown className="w-4 h-4 animate-bounce text-sky-400" />
          </button>
          
          <button 
            onClick={onWhitepaperClick}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-7 py-3.5 rounded-xl glass-soft hover:bg-white/5 text-slate-300 font-bold text-sm transition-all"
          >
            <BookOpen className="w-4 h-4 text-slate-400" />
            <span>Whitepaper & Methodology</span>
          </button>
        </div>

        {/* Methodology Sub-strip */}
        <div className="mt-12 pt-6 border-t border-white/10 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 font-medium">
          <div className="flex items-center space-x-1.5 glass-soft px-3 py-1.5 rounded-full">
            <Shield className="w-3.5 h-3.5 text-sky-400" />
            <span>MoSPI Inflation Aligned</span>
          </div>
          <div className="flex items-center space-x-1.5 glass-soft px-3 py-1.5 rounded-full">
            <Layers className="w-3.5 h-3.5 text-sky-400" />
            <span>GEKS Multilateral Transitivity</span>
          </div>
          <div className="flex items-center space-x-1.5 glass-soft px-3 py-1.5 rounded-full">
            <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
            <span>Daily Automated Scrapers</span>
          </div>
        </div>

      </div>
    </section>
  );
}
