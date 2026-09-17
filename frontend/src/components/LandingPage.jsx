import React from 'react';
import { Plane, ArrowRight } from 'lucide-react';
import Hero from './Hero';
import PipelineSection from './PipelineSection';
import VantaClouds from './VantaClouds';

export default function LandingPage({ onExploreDashboard }) {
  return (
    <VantaClouds className="min-h-screen selection:bg-sky-500 selection:text-white">
      
      {/* Floating Header Bar */}
      <header className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-8 py-3.5 flex items-center justify-between text-slate-900" style={{ background: 'transparent' }}>
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold">
            <Plane className="w-4 h-4 stroke-[2.5]" />
          </div>
          <div>
            <span className="text-base font-extrabold tracking-tight text-slate-900 font-sans">AeroStat</span>
            <span className="hidden sm:inline-block text-xs text-slate-700 ml-2 font-semibold">Real-Time Airfare Intelligence</span>
          </div>
        </div>

        {/* Compact Glass CTA Button */}
        <button
          onClick={onExploreDashboard}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-lg shadow-sky-600/20 transition-all duration-300 group cursor-pointer"
        >
          <span>Explore Dashboard</span>
          <ArrowRight className="w-3.5 h-3.5 text-white group-hover:translate-x-1 transition-transform" />
        </button>
      </header>

      {/* 1. Hero Section */}
      <div className="relative z-10 pt-16">
        <Hero 
          onExploreClick={onExploreDashboard} 
        />
      </div>

      {/* 2. Pipeline Section with Dotted SVG Connecting Path & Scroll-Animated Plane */}
      <div className="relative z-10">
        <PipelineSection />
      </div>

      {/* Bottom CTA Banner */}
      <section className="relative z-10 max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="p-8 sm:p-12 rounded-3xl border border-sky-100 bg-white/85 backdrop-blur-md space-y-6 shadow-xl shadow-sky-900/5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-sky-400/10 rounded-full blur-3xl pointer-events-none" />

          <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-950 font-sans">
            Ready to Explore AeroStat Airfare Intelligence?
          </h3>
          
          <p className="text-xs sm:text-sm text-slate-800 max-w-xl mx-auto leading-relaxed font-medium">
            Access live corridor heatmaps, carrier price trajectory graphs, booking window breakdowns, and full methodology details inside the workspace.
          </p>

          <div className="pt-2 flex justify-center">
            <button
              onClick={onExploreDashboard}
              className="inline-flex items-center space-x-2.5 px-8 py-3.5 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-extrabold text-sm shadow-xl shadow-sky-500/25 hover:shadow-sky-500/40 transition-all transform hover:-translate-y-0.5 cursor-pointer"
            >
              <span>Explore Dashboard</span>
              <ArrowRight className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      </section>

    </VantaClouds>
  );
}
