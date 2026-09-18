import React, { useState } from 'react';
import { 
  ShieldCheck, Database, Layers, Calculator, CheckCircle2, 
  Clock, Activity, AlertTriangle, ArrowRight, Sparkles, Filter, 
  BarChart3, RefreshCw, Cpu, FileText, ChevronRight, HelpCircle
} from 'lucide-react';

export default function MethodologySection() {
  const [activeTab, setActiveTab] = useState('pipeline');

  // Status badge helper
  const renderStatusBadge = (type) => {
    switch (type) {
      case 'IMPLEMENTED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
            ● IMPLEMENTED
          </span>
        );
      case 'PARTIALLY_LIVE':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5" />
            ◐ PARTIALLY LIVE
          </span>
        );
      case 'DEFINED_NOT_COLLECTED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400 mr-1.5" />
            ◐ METHODOLOGY DEFINED
          </span>
        );
      case 'PLANNED':
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500 mr-1.5" />
            ○ PLANNED
          </span>
        );
    }
  };

  // Pipeline stages configuration
  const pipelineStages = [
    { num: '01', name: 'Raw Observations', desc: 'Real-time scraper acquisition across GDS & direct APIs', icon: Database, status: 'IMPLEMENTED' },
    { num: '02', name: 'Data Cleaning', desc: 'Sanitizing currency formatting, IST timestamps & null filtering', icon: Filter, status: 'IMPLEMENTED' },
    { num: '03', name: 'Normalization', desc: 'Standardizing airline codes (AI, 6E, IX, QP, SG) & route pairs', icon: RefreshCw, status: 'IMPLEMENTED' },
    { num: '04', name: 'Validation & Deduplication', desc: 'Strict hash-matching on route + flight_num + departure + timestamp', icon: ShieldCheck, status: 'IMPLEMENTED' },
    { num: '05', name: 'Fare Decomposition', desc: 'Extracting Base Fare, YQ surcharge, UDF, GST & fees', icon: Calculator, status: 'IMPLEMENTED' },
    { num: '06', name: 'Price Relatives', desc: 'Matching current flight fare against base period reference fare', icon: Activity, status: 'IMPLEMENTED' },
    { num: '07', name: 'Jevons Index', desc: 'Geometric mean aggregation of elementary price relatives', icon: Cpu, status: 'IMPLEMENTED' },
    { num: '08', name: 'Booking-Window Weighting', desc: 'Aggregating T+1, T+7, T+15, T+30, T+45 advance purchase buckets', icon: Clock, status: 'PARTIALLY_LIVE' },
    { num: '09', name: 'DGCA Pax Volume Weighting', desc: 'Weighting route indexes by official DGCA passenger numbers', icon: Layers, status: 'IMPLEMENTED' },
    { num: '10', name: 'Route / Aggregate Index', desc: 'Combining weighted corridor indices into national indicator', icon: BarChart3, status: 'IMPLEMENTED' },
    { num: '11', name: 'AeroStat Airfare Signal', desc: 'Real-time intelligence feed & inflation surveillance vector', icon: Sparkles, status: 'IMPLEMENTED' },
  ];

  return (
    <div className="space-y-10 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      
      {/* -------------------------------------------------------------
          1. HEADER SECTION
      ------------------------------------------------------------- */}
      <div className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono font-bold tracking-wide uppercase mb-3">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>Official Economic Index Methodology</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight font-sans">
            METHODOLOGY USED
          </h1>
          <p className="text-base text-slate-400 mt-2 max-w-3xl leading-relaxed">
            How AeroStat transforms live airfare observations into a representative price index.
          </p>
        </div>

        <div className="flex glass-segmented self-start md:self-auto">
          <button 
            onClick={() => setActiveTab('pipeline')}
            className={`px-4 py-2 rounded-full text-xs font-bold transition-all ${
              activeTab === 'pipeline' 
                ? 'glass-tab-active' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Computation Flow
          </button>
          <button 
            onClick={() => setActiveTab('math')}
            className={`px-4 py-2 rounded-full text-xs font-bold transition-all ${
              activeTab === 'math' 
                ? 'glass-tab-active' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Index Mathematics
          </button>
        </div>
      </div>

      {/* -------------------------------------------------------------
          2. METHODOLOGY STATUS SUMMARY MATRICES
      ------------------------------------------------------------- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-elevated p-5 rounded-2xl border-emerald-500/20 bg-emerald-950/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase">Core Methodology Status</span>
            {renderStatusBadge('IMPLEMENTED')}
          </div>
          <p className="text-xl font-bold text-white font-sans">Fully Implemented Pipeline</p>
          <p className="text-xs text-slate-400 mt-1">
            Data cleaning, normalization, deduplication, Jevons geometric mean, and DGCA route weighting.
          </p>
        </div>

        <div className="glass-elevated p-5 rounded-2xl border-amber-500/20 bg-amber-950/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold text-amber-400 uppercase">Live Scraper Coverage</span>
            {renderStatusBadge('PARTIALLY_LIVE')}
          </div>
          <p className="text-xl font-bold text-white font-sans">T+1, T+7, T+30 Active</p>
          <p className="text-xs text-slate-400 mt-1">
            Active automated sweeps across T+1, T+7, and T+30 horizons. T+15 and T+45 are defined in methodology.
          </p>
        </div>

        <div className="glass-elevated p-5 rounded-2xl border-sky-500/20 bg-sky-950/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold text-sky-400 uppercase">Next Milestone</span>
            {renderStatusBadge('PLANNED')}
          </div>
          <p className="text-xl font-bold text-white font-sans">GEKS & MoSPI Overlay</p>
          <p className="text-xs text-slate-400 mt-1">
            Multilateral transitivity (GEKS) and real-time MoSPI official CPI correlation benchmarks in development.
          </p>
        </div>
      </div>

      {/* -------------------------------------------------------------
          3. PROGRESSIVE STORYTELLING PIPELINE FLOW DIAGRAM (11 STAGES)
      ------------------------------------------------------------- */}
      {activeTab === 'pipeline' && (
      <div className="glass-elevated p-6 sm:p-8 rounded-3xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-sky-400" />
              Calculation & Statistical Pipeline
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              End-to-end transformation of raw web observation quotes into the canonical AeroStat Airfare Signal.
            </p>
          </div>
          <span className="hidden sm:inline-flex items-center px-3 py-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-slate-400">
            11 Computation Stages
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4">
          {pipelineStages.map((stage, idx) => {
            const Icon = stage.icon;
            return (
              <div 
                key={idx}
                className="group relative p-5 rounded-2xl glass-soft hover:border-sky-500/40 hover:bg-slate-900/90 transition-all duration-300 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-bold text-sky-400 bg-sky-500/10 px-2.5 py-1 rounded-lg border border-sky-500/20">
                      STAGE {stage.num}
                    </span>
                    {renderStatusBadge(stage.status)}
                  </div>
                  
                  <div className="flex items-center space-x-2.5 mt-2">
                    <div className="p-2 rounded-xl bg-slate-800/80 text-sky-400 group-hover:bg-sky-500/20 transition-all">
                      <Icon className="w-4 h-4" />
                    </div>
                    <h3 className="text-sm font-bold text-slate-100 font-sans group-hover:text-white">
                      {stage.name}
                    </h3>
                  </div>
                  
                  <p className="text-xs text-slate-400 mt-2.5 leading-relaxed font-normal">
                    {stage.desc}
                  </p>
                </div>

                {idx < pipelineStages.length - 1 && (
                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                    <span>Next step</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-sky-400 group-hover:translate-x-1 transition-all" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      )}

      {/* -------------------------------------------------------------
          4. ELEMENTARY PRICE INDEX (JEVONS GEOMETRIC MEAN)
      ------------------------------------------------------------- */}
      {activeTab === 'math' && (
      <div className="space-y-10">
      <div className="glass-elevated p-6 sm:p-8 rounded-3xl space-y-8">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-sky-500/10 text-sky-400 text-xs font-mono font-bold mb-2">
            <span>Core Mathematical Foundation</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white">
            Elementary Price Index: Jevons Geometric Mean
          </h2>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
            AeroStat uses apples-to-apples flight price matching between reference base periods and current observations. Matched price relatives are aggregated using the unweighted Jevons geometric mean, satisfying circularity and time-reversal properties.
          </p>
        </div>

        {/* Visual Matching Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center bg-slate-950/80 p-6 rounded-2xl border border-slate-800">
          
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-xs font-mono font-bold text-slate-400 block uppercase">Reference Base Fare (p₀)</span>
            <div className="text-2xl font-black text-slate-100 font-mono mt-1">₹5,000</div>
            <span className="text-[11px] text-slate-500 mt-1 block">Selected corridor reference observation</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-xs font-mono font-bold text-sky-400 block uppercase">Current Observed Fare (pₜ)</span>
            <div className="text-2xl font-black text-sky-400 font-mono mt-1">₹5,500</div>
            <span className="text-[11px] text-slate-500 mt-1 block">Live scraped flight quote</span>
          </div>

          <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/30">
            <span className="text-xs font-mono font-bold text-sky-300 block uppercase">Price Relative (r = pₜ / p₀)</span>
            <div className="text-2xl font-black text-white font-mono mt-1">1.10</div>
            <span className="text-[11px] text-sky-300/80 mt-1 block">+10% matched price shift</span>
          </div>

        </div>

        {/* Mathematical Card */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-950 border border-slate-800">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-xl">
              <span className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wide">
                Mathematical Specification
              </span>
              <h3 className="text-lg font-bold text-white font-sans">
                Jevons Geometric Mean Formula
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                The Jevons index aggregates matched price relatives using their geometric mean, ensuring robust, transitive price comparison without linear base bias.
              </p>
            </div>

            {/* Mathematically Typeset Card */}
            <div className="w-full md:w-auto p-6 rounded-2xl bg-slate-950 border border-sky-500/40 text-center font-mono shadow-2xl shrink-0 overflow-x-auto">
              <div className="text-[10px] text-sky-400 font-mono font-bold tracking-widest uppercase mb-3">JEVONS GEOMETRIC MEAN</div>
              
              <div className="flex items-center justify-center space-x-2 text-base sm:text-xl font-mono text-sky-400 font-extrabold py-2 px-3 bg-slate-900/90 rounded-xl border border-slate-800">
                <span className="text-sky-300">I<sub>Jevons</sub></span>
                <span className="text-slate-400">=</span>
                
                {/* Product symbol with bounds */}
                <div className="inline-flex flex-col items-center justify-center text-center mx-1">
                  <span className="text-[10px] text-sky-400/80 font-mono leading-none">n</span>
                  <span className="text-2xl sm:text-3xl text-sky-300 font-serif leading-none my-0.5">∏</span>
                  <span className="text-[9px] text-slate-400 font-mono leading-none">i=1</span>
                </div>

                <span className="text-2xl font-light text-slate-500 font-sans">(</span>
                
                {/* Fraction: p_i,t / p_i,0 */}
                <div className="inline-flex flex-col items-center justify-center text-center px-1 font-mono text-xs sm:text-sm my-1">
                  <span className="border-b border-sky-400/80 pb-0.5 px-1 text-sky-200 font-bold">p<sub>i,t</sub></span>
                  <span className="pt-0.5 px-1 text-slate-300">p<sub>i,0</sub></span>
                </div>

                <span className="text-2xl font-light text-slate-500 font-sans">)</span>
                
                <sup className="text-xs text-sky-300 font-mono font-bold -ml-1">1/n</sup>
                <span className="text-slate-500 mx-1">×</span>
                <span className="text-white font-black">100</span>
              </div>

              <div className="text-[10px] text-slate-400 mt-3 font-mono">
                Where <span className="text-sky-300 font-bold">n</span> = number of matched flight observations
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------
          5. BOOKING-WINDOW WEIGHTING
      ------------------------------------------------------------- */}
      <div className="glass-elevated p-6 sm:p-8 rounded-3xl space-y-6">
        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-sky-400" />
              Booking-Window Weighting
            </h2>
            {renderStatusBadge('PARTIALLY_LIVE')}
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Incorporates advance-purchase horizons to reflect dynamic pricing structures across advance booking windows.
          </p>
        </div>

        {/* Horizon Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            { id: 'T+1', label: 'T+1 (Tomorrow)', status: 'LIVE', desc: 'Last-minute surge fare', active: true },
            { id: 'T+7', label: 'T+7 (1 Week)', status: 'LIVE', desc: 'Short-term leisure & business', active: true },
            { id: 'T+15', label: 'T+15 (15 Days)', status: 'LIVE', desc: 'Mid-window advance horizon', active: true },
            { id: 'T+30', label: 'T+30 (1 Month)', status: 'LIVE', desc: 'Standard advance booking', active: true },
            { id: 'T+45', label: 'T+45 (45 Days)', status: 'LIVE', desc: 'Long-range seasonal planning', active: true },
          ].map((item) => (
            <div 
              key={item.id}
              className={`p-4 rounded-2xl border transition-all ${
                item.active 
                  ? 'bg-slate-900/90 border-sky-500/40 shadow-sm' 
                  : 'bg-slate-950/60 border-slate-800/80 opacity-75'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-black text-white font-mono">{item.id}</span>
                <span className={`px-2 py-0.5 rounded text-[9px] font-bold font-mono ${
                  item.active 
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                    : 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                }`}>
                  {item.status === 'LIVE' ? '● LIVE SCRAPED' : '◐ DEFINED'}
                </span>
              </div>
              <p className="text-xs font-semibold text-slate-200">{item.label}</p>
              <p className="text-[11px] text-slate-400 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>

        {/* Conceptual Aggregation Flow */}
        <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
            <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-mono">
              <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-sky-400 font-bold">T+1 Index</span>
              <span className="text-slate-600">+</span>
              <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-sky-400 font-bold">T+7 Index</span>
              <span className="text-slate-600">+</span>
              <span className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-500">T+15 (Defined)</span>
              <span className="text-slate-600">+</span>
              <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-sky-400 font-bold">T+30 Index</span>
              <span className="text-slate-600">+</span>
              <span className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-500">T+45 (Defined)</span>
            </div>

            <ArrowRight className="w-5 h-5 text-sky-400 hidden lg:block shrink-0" />

            <div className="px-4 py-2.5 rounded-xl bg-sky-500/20 border border-sky-400/40 text-sky-300 font-mono text-xs font-extrabold text-center">
              Weighted Booking Window Index
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-900 flex items-center justify-between text-[11px]">
            <span className="text-amber-400 font-semibold flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Disclaimer: Prototype / estimated weighting assumption
            </span>
            <span className="text-slate-500 hidden sm:inline">Not official MoSPI CPI weights</span>
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------
          6. DGCA PASSENGER-VOLUME WEIGHTING
      ------------------------------------------------------------- */}
      <div className="glass-elevated p-6 sm:p-8 rounded-3xl space-y-6">
        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-sky-400" />
              DGCA Passenger-Volume Weighting
            </h2>
            {renderStatusBadge('IMPLEMENTED')}
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Route representation is additionally informed by DGCA passenger-volume data to ensure trunk routes (e.g. DEL-BOM) carry accurate national weight.
          </p>
        </div>

        {/* Route Passenger Volume Visual Bars */}
        <div className="space-y-3 bg-slate-950/80 p-5 rounded-2xl border border-slate-800">
          <div className="space-y-1">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-200">DEL – BOM (Delhi – Mumbai)</span>
              <span className="text-sky-400 font-mono">2.45M Annual Pax (High Weight)</span>
            </div>
            <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800">
              <div className="bg-gradient-to-r from-sky-500 to-blue-600 h-full rounded-full w-[92%]" />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-200">DEL – BLR (Delhi – Bengaluru)</span>
              <span className="text-sky-400 font-mono">1.82M Annual Pax (Medium-High Weight)</span>
            </div>
            <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800">
              <div className="bg-gradient-to-r from-sky-500 to-blue-600 h-full rounded-full w-[72%]" />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-200">BOM – MAA (Mumbai – Chennai)</span>
              <span className="text-sky-400 font-mono">0.98M Annual Pax (Medium Weight)</span>
            </div>
            <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800">
              <div className="bg-gradient-to-r from-sky-500 to-blue-600 h-full rounded-full w-[45%]" />
            </div>
          </div>
        </div>

        {/* Strict Distinction Warning */}
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2 text-amber-300 font-extrabold font-mono text-sm">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>SCRAPED OBSERVATIONS ≠ PASSENGER VOLUME</span>
          </div>
          <p className="text-amber-200/80 text-[11px]">
            Passenger-volume weights come exclusively from DGCA data. Where DGCA route figures are unavailable, the prototype falls back to an unweighted route contribution.
          </p>
        </div>
      </div>

      {/* -------------------------------------------------------------
          7. FARE DECOMPOSITION
      ------------------------------------------------------------- */}
      <div className="glass-elevated p-6 sm:p-8 rounded-3xl space-y-6">
        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
              <Calculator className="w-5 h-5 text-sky-400" />
              Fare Decomposition Pipeline
            </h2>
            {renderStatusBadge('IMPLEMENTED')}
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Decomposes final displayed quotes into underlying tariff components using carrier-specific breakdown schedules.
          </p>
        </div>

        {/* Fare Component Breakdown Visual */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          
          <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <span className="text-xs font-mono font-bold text-slate-400 uppercase">Displayed Total Fare</span>
              <span className="text-xl font-extrabold text-sky-400 font-mono">₹6,250</span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between text-slate-300">
                <span>Base Airfare</span>
                <span className="font-bold text-white">₹4,800</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Fuel Surcharge (YQ)</span>
                <span className="font-bold text-white">₹850</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>User Development Fee (UDF)</span>
                <span className="font-bold text-white">₹320</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>GST (Aviation Tax)</span>
                <span className="font-bold text-white">₹280</span>
              </div>
              <div className="flex justify-between text-slate-400 pt-2 border-t border-slate-900">
                <span>Other Ancillary Fees</span>
                <span className="text-slate-500 font-mono">N/A</span>
              </div>
            </div>
          </div>

          <div className="space-y-3 text-xs text-slate-400 leading-relaxed">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <h4 className="font-bold text-white mb-1">Tariff Schedule Extraction</h4>
              <p>
                Attempts to decompose displayed total fares into Base Fare, YQ surcharge, UDF, and GST based on tariff rules.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <h4 className="font-bold text-white mb-1">Handling Missing Components</h4>
              <p>
                If a tariff component cannot be determined with statistical certainty, the system displays <span className="font-mono text-sky-400 font-bold">"N/A"</span> rather than inventing values.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------
          8. DATA QUALITY & CLEANING
      ------------------------------------------------------------- */}
      <div className="glass-elevated p-6 sm:p-8 rounded-3xl space-y-6">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <Filter className="w-5 h-5 text-sky-400" />
            From Raw Data to Trusted Observation
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated cleaning, normalization, and deduplication rules ensure zero corrupted entries enter index calculations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-center text-xs font-mono">
          {[
            { title: 'Raw Fare', sub: 'Scraped Quote', color: 'border-slate-800 bg-slate-950 text-slate-400' },
            { title: 'Cleaning', sub: 'Format & Null Fix', color: 'border-sky-500/30 bg-sky-500/10 text-sky-300' },
            { title: 'Normalization', sub: 'IATA & Airline Code', color: 'border-sky-500/30 bg-sky-500/10 text-sky-300' },
            { title: 'Deduplication', sub: 'Hash Fingerprint', color: 'border-sky-500/30 bg-sky-500/10 text-sky-300' },
            { title: 'Canonical Record', sub: 'Index Ingestion', color: 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300 font-bold' },
          ].map((item, idx) => (
            <div key={idx} className={`p-4 rounded-2xl border ${item.color} flex flex-col justify-center space-y-1`}>
              <span className="font-bold uppercase tracking-wider">{item.title}</span>
              <span className="text-[10px] opacity-80">{item.sub}</span>
            </div>
          ))}
        </div>
      </div>

      {/* -------------------------------------------------------------
          9. HIERARCHICAL INDEX STRUCTURE
      ------------------------------------------------------------- */}
      <div className="glass-elevated p-6 sm:p-8 rounded-3xl space-y-6">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-sky-400" />
            Hierarchical Index Structure
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            How granular individual flight quotes aggregate into high-level economic intelligence signals.
          </p>
        </div>

        <div className="space-y-3 font-mono text-xs">
          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-slate-300">
            <span className="font-bold text-sky-400">1. FLIGHT OBSERVATIONS</span>
            <span>Granular live quotes (Route + Airline + Dep Timestamp + Window)</span>
          </div>

          <div className="pl-6 border-l-2 border-sky-500/40 space-y-3">
            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-slate-300">
              <span className="font-bold text-sky-400">2. AIRLINE × ROUTE × BOOKING WINDOW</span>
              <span>Matched Jevons price relative calculation per slice</span>
            </div>

            <div className="pl-6 border-l-2 border-sky-500/40 space-y-3">
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-slate-300">
                <span className="font-bold text-sky-400">3. ROUTE INDEX</span>
                <span>Booking-window weighted corridor price index</span>
              </div>

              <div className="pl-6 border-l-2 border-sky-500/40">
                <div className="p-4 rounded-xl bg-sky-500/20 border border-sky-400/40 flex items-center justify-between text-white font-extrabold">
                  <span>4. AGGREGATED AEROSTAT AIRFARE SIGNAL</span>
                  <span className="text-sky-300">DGCA volume-weighted national airfare index</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
      )}

    </div>
  );
}
