import React, { useState, useEffect } from 'react';
import { Plane, Activity, FileText, ChevronRight, BarChart3, ShieldCheck, ArrowUpRight } from 'lucide-react';

export default function Header({ onOpenWhitepaper, onScrollToDashboard }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled 
        ? 'bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 py-3 shadow-2xl shadow-sky-950/30' 
        : 'bg-transparent py-5'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        
        {/* Brand / Logo */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold transform transition hover:scale-105">
            <Plane className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-extrabold tracking-tight text-white font-sans">APEX-IND</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 mr-1.5 animate-pulse"></span>
                LIVE BENCHMARK
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium hidden sm:block">India Real-Time Airfare Intelligence</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden lg:flex items-center space-x-8 text-sm font-medium text-slate-300">
          <a href="#pipeline" className="hover:text-sky-400 transition-colors">Ingestion</a>
          <a href="#deduplication" className="hover:text-sky-400 transition-colors">Ancillary Noise</a>
          <a href="#booking-windows" className="hover:text-sky-400 transition-colors">T-0..T-45 Windows</a>
          <a href="#geks-methodology" className="hover:text-sky-400 transition-colors">GEKS Index</a>
          <a href="#mospi-calibration" className="hover:text-sky-400 transition-colors">MoSPI Benchmark</a>
          <a href="#dashboard" className="hover:text-sky-400 transition-colors flex items-center gap-1 font-semibold text-sky-400">
            <BarChart3 className="w-4 h-4" /> Live Dashboard
          </a>
        </nav>

        {/* CTA Buttons */}
        <div className="flex items-center space-x-3">
          <button 
            onClick={onOpenWhitepaper}
            className="hidden sm:flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg text-slate-200 bg-slate-900 border border-slate-700/80 hover:bg-slate-800 hover:border-slate-600 transition-all shadow-sm"
          >
            <FileText className="w-3.5 h-3.5 text-sky-400" />
            <span>Whitepaper</span>
          </button>
          
          <button 
            onClick={onScrollToDashboard}
            className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold rounded-lg text-white bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 shadow-md shadow-sky-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>Launch Dashboard</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </header>
  );
}
