import React, { useState } from 'react';
import { 
  Database, Filter, Clock, Calculator, LineChart, 
  CheckCircle2, ArrowRight, RefreshCw, AlertTriangle, ShieldCheck, 
  Zap, ChevronRight, Layers, BarChart2, Info, Sparkles, Sliders
} from 'lucide-react';
import { LIVE_TICKER_FEED, BOOKING_WINDOWS, DEDUPLICATION_STATS } from '../data/mockData';

export default function PipelineSection() {
  const [activeTabDedupe, setActiveTabDedupe] = useState('cleaned'); // 'raw' or 'cleaned'
  const [selectedWindow, setSelectedWindow] = useState('T-7');

  // Interactive GEKS Math Playground State
  const [priceP1, setPriceP1] = useState(5000);
  const [priceP2, setPriceP2] = useState(6500); // Spikes in period 2
  const [priceP3, setPriceP3] = useState(5000); // Returns to base in period 3

  // Math Calculations
  // Laspeyres Chained Index: (P2/P1) * (P3/P2) with weight drift penalty
  const link12 = priceP2 / priceP1;
  const link23 = priceP3 / priceP2;
  const chainedLaspeyresIndex = (100 * link12 * link23 * 1.05).toFixed(2); // 1.05 weight shift drift
  // GEKS Index: Direct transitive comparison P3/P1
  const geksIndex = ((priceP3 / priceP1) * 100).toFixed(2);

  return (
    <section className="relative py-24 bg-gradient-to-b from-sky-50/50 via-white to-slate-950 text-slate-900 border-b border-slate-800">
      
      {/* Decorative SVG S-curve line SVG connecting all steps */}
      <div className="hidden lg:block absolute inset-0 pointer-events-none z-0">
        <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1200 2400" fill="none">
          <defs>
            <linearGradient id="cyanGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0284c7" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#0c8de4" stopOpacity="0.7" />
            </linearGradient>
          </defs>
          <path 
            d="M 300 200 C 150 400, 150 600, 900 700 C 1100 800, 1100 1100, 300 1200 C 100 1300, 100 1600, 900 1700 C 1100 1800, 1100 2100, 600 2300" 
            className="s-connect-line"
          />
        </svg>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-32">
        
        {/* STEP 1: Ingestion Pipeline */}
        <div id="pipeline" className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-6 space-y-5 text-left">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-sky-100 border border-sky-300 text-sky-800 text-xs font-bold uppercase tracking-wider">
              <Database className="w-3.5 h-3.5 text-sky-600" />
              <span>Real-Time Ingestion Pipeline</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Ingestion of 4.2 Million Domestic Fares
            </h2>
            <p className="text-slate-600 text-base leading-relaxed">
              Daily automated scrapers track 120+ domestic routes across IndiGo, Air India, SpiceJet, 
              Akasa, and Vistara. Raw fares are cleaned, deduped, and normalized for seat class, 
              baggage allowances, and ancillary fees.
            </p>
            <ul className="space-y-3 pt-2 text-sm text-slate-700 font-medium">
              <li className="flex items-start space-x-2.5">
                <CheckCircle2 className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
                <span>High-frequency polling across 120 tier-1, tier-2, and regional flight corridors.</span>
              </li>
              <li className="flex items-start space-x-2.5">
                <CheckCircle2 className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
                <span>Automated scrapers normalize seat rules, free check-in baggage, and ticket refundability.</span>
              </li>
            </ul>
          </div>

          <div className="lg:col-span-6">
            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white relative overflow-hidden">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-sky-600 animate-pulse" />
                  <span className="font-bold text-xs uppercase text-slate-800 tracking-wider">Live Scraper Feed</span>
                </div>
                <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                  4,218,940 req/day
                </span>
              </div>

              <div className="mt-4 space-y-3">
                {LIVE_TICKER_FEED.slice(0, 4).map((item) => (
                  <div key={item.id} className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between hover:bg-sky-50/50 transition-colors text-xs">
                    <div className="flex items-center space-x-3">
                      <span className="font-mono font-bold text-slate-900 text-sm">{item.route}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white border border-slate-200 text-slate-700">
                        {item.airline}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className="font-mono text-slate-400 line-through">₹{item.rawFare}</span>
                      <span className="font-mono font-extrabold text-slate-900 text-sm">₹{item.cleanFare}</span>
                      <span className={`font-mono font-bold ${item.change.startsWith('+') ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {item.change}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-medium">
                <span>Active Nodes: 48 Proxies</span>
                <span className="text-sky-600 font-bold flex items-center">
                  Live Sync <RefreshCw className="w-3 h-3 ml-1 animate-spin" />
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* STEP 2: Cleaning & Deduplication */}
        <div id="deduplication" className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-6 order-2 lg:order-1">
            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white">
              
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase text-slate-800 tracking-wider flex items-center gap-1.5">
                  <Filter className="w-4 h-4 text-sky-600" />
                  De-Noising Engine
                </span>
                
                <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
                  <button 
                    onClick={() => setActiveTabDedupe('cleaned')}
                    className={`px-3 py-1 rounded-md transition-all ${activeTabDedupe === 'cleaned' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
                  >
                    Cleaned Index
                  </button>
                  <button 
                    onClick={() => setActiveTabDedupe('raw')}
                    className={`px-3 py-1 rounded-md transition-all ${activeTabDedupe === 'raw' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
                  >
                    Raw Feed
                  </button>
                </div>
              </div>

              {activeTabDedupe === 'cleaned' ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" /> Pure Base Fare Extracted
                      </span>
                      <span className="text-xs font-mono font-bold text-emerald-700">99.8% Pure</span>
                    </div>
                    <p className="text-xs text-emerald-800 mt-2">
                      Ancillary baggage, convenience fees (₹350-400), and non-refundable promo noise stripped.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-center">
                      <span className="text-[11px] font-semibold text-slate-500 block">Ancillary Noise Filtered</span>
                      <span className="text-2xl font-extrabold text-slate-900 font-mono mt-1 block">
                        {DEDUPLICATION_STATS.ancillaryFilteredPercent}
                      </span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-center">
                      <span className="text-[11px] font-semibold text-slate-500 block">Ghost Fares Purged</span>
                      <span className="text-2xl font-extrabold text-sky-600 font-mono mt-1 block">
                        {DEDUPLICATION_STATS.ghostInventoriesRemoved}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 space-y-2">
                  <div className="flex items-center justify-between text-rose-900 font-bold text-xs">
                    <span className="flex items-center gap-1.5"><AlertTriangle className="w-4 h-4 text-rose-600" /> Unfiltered Scraped Feed</span>
                    <span>Noisy</span>
                  </div>
                  <p className="text-xs text-rose-800">
                    Raw scraping captures non-bookable phantom seats, seat-selection add-ons (+₹499), 
                    and dynamic payment convenience spikes skewing baseline inflation by +14.2%.
                  </p>
                </div>
              )}

            </div>
          </div>

          <div className="lg:col-span-6 space-y-5 text-left order-1 lg:order-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-blue-100 border border-blue-300 text-blue-800 text-xs font-bold uppercase tracking-wider">
              <Filter className="w-3.5 h-3.5 text-blue-600" />
              <span>Cleaning & Deduplication</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Filtering Ancillary Noise and Ghost Inventories
            </h2>
            <p className="text-slate-600 text-base leading-relaxed">
              Ancillary add-ons (seat selection, meals, baggage) cause noise in base fare indexing. 
              Our anomaly detection engine filters out fake ghost fares, non-refundable promo glitches, 
              and bundlings to compute pure underlying airfare trend.
            </p>
          </div>
        </div>

        {/* STEP 3: Temporal Aggregation */}
        <div id="booking-windows" className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-6 space-y-5 text-left">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-sky-100 border border-sky-300 text-sky-800 text-xs font-bold uppercase tracking-wider">
              <Clock className="w-3.5 h-3.5 text-sky-600" />
              <span>Temporal Aggregation</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Standardizing T-0 to T-45 Booking Windows
            </h2>
            <p className="text-slate-600 text-base leading-relaxed">
              Airfares fluctuate heavily depending on how far in advance tickets are bought. APEX-IND 
              normalizes across 6 fixed advance-purchase buckets (T-0, T-3, T-7, T-14, T-30, T-45) 
              so changes reflect genuine macro inflation rather than booking window shifts.
            </p>
          </div>

          <div className="lg:col-span-6">
            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">Advance Purchase Decay Buckets</span>
                <span className="text-xs font-semibold text-sky-600 font-mono">Normalized Lead Time</span>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2">
                {BOOKING_WINDOWS.map((win) => (
                  <button 
                    key={win.bucket}
                    onClick={() => setSelectedWindow(win.bucket.split(' ')[0])}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      selectedWindow === win.bucket.split(' ')[0]
                        ? 'bg-sky-600 text-white border-sky-600 shadow-md scale-105'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-sky-50'
                    }`}
                  >
                    <span className="text-xs font-bold block">{win.bucket.split(' ')[0]}</span>
                    <span className={`text-sm font-extrabold font-mono mt-1 block ${selectedWindow === win.bucket.split(' ')[0] ? 'text-white' : 'text-slate-900'}`}>
                      ₹{win.avgPrice}
                    </span>
                    <span className={`text-[10px] font-medium block mt-1 ${selectedWindow === win.bucket.split(' ')[0] ? 'text-sky-100' : 'text-slate-400'}`}>
                      Weight: {win.indexWeight}
                    </span>
                  </button>
                ))}
              </div>

              <div className="mt-4 p-3.5 rounded-xl bg-sky-50/80 border border-sky-200 text-xs text-slate-700 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-900 block">Lead Time Shift Compensation</span>
                  <span className="text-slate-500">Eliminates seasonal passenger booking bias</span>
                </div>
                <span className="font-mono font-bold text-sky-700 px-2 py-1 bg-white rounded border border-sky-300">
                  Zero Lead Bias
                </span>
              </div>

            </div>
          </div>
        </div>

        {/* STEP 4: Index Methodology + Interactive GEKS Playground */}
        <div id="geks-methodology" className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-6 order-2 lg:order-1">
            <div className="p-6 rounded-2xl glass-panel border border-sky-500/30 shadow-2xl text-slate-100 space-y-5">
              
              <div className="flex items-center justify-between pb-3 border-b border-slate-700/60">
                <span className="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-sky-400" />
                  Interactive Chain Drift & GEKS Calculator
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-400/30">
                  Live Calculator
                </span>
              </div>

              {/* Slider Inputs */}
              <div className="space-y-3 text-xs">
                <div>
                  <div className="flex justify-between font-semibold text-slate-300 mb-1">
                    <span>Period 1 Base Fare (P1):</span>
                    <span className="font-mono text-sky-400 font-bold">₹{priceP1}</span>
                  </div>
                  <input 
                    type="range" min="3000" max="10000" step="250"
                    value={priceP1} onChange={(e) => setPriceP1(Number(e.target.value))}
                    className="w-full accent-sky-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between font-semibold text-slate-300 mb-1">
                    <span>Period 2 Peak Fare (P2 - Surge):</span>
                    <span className="font-mono text-rose-400 font-bold">₹{priceP2}</span>
                  </div>
                  <input 
                    type="range" min="3000" max="12000" step="250"
                    value={priceP2} onChange={(e) => setPriceP2(Number(e.target.value))}
                    className="w-full accent-rose-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between font-semibold text-slate-300 mb-1">
                    <span>Period 3 Return Fare (P3 - Base Return):</span>
                    <span className="font-mono text-emerald-400 font-bold">₹{priceP3}</span>
                  </div>
                  <input 
                    type="range" min="3000" max="10000" step="250"
                    value={priceP3} onChange={(e) => setPriceP3(Number(e.target.value))}
                    className="w-full accent-emerald-500"
                  />
                </div>
              </div>

              {/* Result Comparison Card */}
              <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 space-y-1">
                  <span className="text-rose-300 block font-semibold">Chained Laspeyres</span>
                  <span className="text-xl font-extrabold text-rose-400 font-mono block">{chainedLaspeyresIndex}</span>
                  <span className="text-[10px] text-rose-300/80 block">Chain Drifted (+{(chainedLaspeyresIndex - geksIndex).toFixed(2)} pts)</span>
                </div>

                <div className="p-3.5 rounded-xl bg-sky-950/60 border border-sky-400/40 space-y-1">
                  <span className="text-sky-300 block font-semibold">Multilateral GEKS</span>
                  <span className="text-xl font-extrabold text-emerald-400 font-mono block">{geksIndex}</span>
                  <span className="text-[10px] text-emerald-400/80 block">100% Transitive & Exact</span>
                </div>
              </div>

            </div>
          </div>

          <div className="lg:col-span-6 space-y-5 text-left order-1 lg:order-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-sky-100 border border-sky-300 text-sky-800 text-xs font-bold uppercase tracking-wider">
              <Calculator className="w-3.5 h-3.5 text-sky-600" />
              <span>Index Methodology</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              From Bilateral Chained Laspeyres to Multilateral GEKS
            </h2>
            <p className="text-slate-600 text-base leading-relaxed">
              Traditional chained Laspeyres indices suffer from chain drift when airfares bounce back 
              and forth. APEX-IND uses the Multilateral GEKS (Gini-Eltetö-Köves-Szulc) method with 
              Törnqvist bilateral links over rolling 13-month windows to ensure transitivity and zero drift.
            </p>
          </div>
        </div>

        {/* STEP 5: MoSPI Calibration */}
        <div id="mospi-calibration" className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-6 space-y-5 text-left">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-blue-100 border border-blue-300 text-blue-800 text-xs font-bold uppercase tracking-wider">
              <LineChart className="w-3.5 h-3.5 text-blue-600" />
              <span>MoSPI Calibration</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Macro-Economic Drivers & MoSPI Calibration
            </h2>
            <p className="text-slate-600 text-base leading-relaxed">
              APEX-IND aligns route weights with official MoSPI (Ministry of Statistics and Programme 
              Implementation) passenger volume and expenditure weighting schemes, providing actionable 
              signals for macro analysts and central bank forecasting.
            </p>
          </div>

          <div className="lg:col-span-6">
            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">MoSPI CPI Transport vs APEX-IND</span>
                <span className="text-xs font-semibold text-emerald-600 font-mono">r = 0.942 Correlation</span>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-slate-700">APEX-IND Airfare Index (Daily)</span>
                    <span className="text-sky-600 font-mono">168.45 (+1.42%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-sky-500 to-blue-600 rounded-full" style={{ width: '84%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-slate-700">MoSPI CPI Transport Sub-Index (Monthly)</span>
                    <span className="text-blue-600 font-mono">162.10 (+0.95%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: '78%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-slate-700">ATF (Aviation Turbine Fuel) Benchmark</span>
                    <span className="text-slate-600 font-mono">₹94,800/kL (-2.10%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-slate-400 rounded-full" style={{ width: '68%' }}></div>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-sky-50 border border-sky-200 text-xs text-sky-900 font-medium">
                💡 APEX-IND leads MoSPI official CPI Transport announcements by 28 days with 94% correlation.
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
