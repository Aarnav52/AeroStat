import React, { useState } from 'react';
import {
  Database,
  Filter,
  Clock,
  Calculator,
  LineChart,
  CheckCircle2,
  RefreshCw,
  AlertTriangle,
  ShieldCheck,
  Zap,
  Sliders,
  Plane,
  Server,
  BarChart3
} from 'lucide-react';

export default function PipelineSection() {
  const [activeTabDedupe, setActiveTabDedupe] = useState('cleaned');
  const [selectedWindow, setSelectedWindow] = useState('T+1');

  // ---------------------------------------------------------
  // GEKS METHODOLOGY DEMONSTRATION
  // This is only an educational demonstration.
  // It is NOT the production index calculated by the backend.
  // ---------------------------------------------------------

  const [priceP1, setPriceP1] = useState(5000);
  const [priceP2, setPriceP2] = useState(6500);
  const [priceP3, setPriceP3] = useState(5000);

  const geksIndex = ((priceP3 / priceP1) * 100).toFixed(2);

  return (
    <section className="relative py-24 bg-gradient-to-b from-sky-50/50 via-white to-slate-950 text-slate-900 border-b border-slate-800">

      {/* Decorative SVG connector */}
      <div className="hidden lg:block absolute inset-0 pointer-events-none z-0">
        <svg
          className="w-full h-full"
          preserveAspectRatio="none"
          viewBox="0 0 1200 2400"
          fill="none"
        >
          <defs>
            <linearGradient
              id="cyanGradient"
              x1="0%"
              y1="0%"
              x2="0%"
              y2="100%"
            >
              <stop
                offset="0%"
                stopColor="#0284c7"
                stopOpacity="0.8"
              />
              <stop
                offset="50%"
                stopColor="#38bdf8"
                stopOpacity="0.9"
              />
              <stop
                offset="100%"
                stopColor="#0c8de4"
                stopOpacity="0.7"
              />
            </linearGradient>
          </defs>

          <path
            d="M 300 200 C 150 400, 150 600, 900 700 C 1100 800, 1100 1100, 300 1200 C 100 1300, 100 1600, 900 1700 C 1100 1800, 1100 2100, 600 2300"
            className="s-connect-line"
          />
        </svg>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-32">

        {/* =====================================================
            STEP 1 — DATA ACQUISITION
        ====================================================== */}

        <div
          id="pipeline"
          className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center"
        >

          <div className="lg:col-span-6 space-y-5 text-left">

            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-sky-100 border border-sky-300 text-sky-800 text-xs font-bold uppercase tracking-wider">
              <Database className="w-3.5 h-3.5 text-sky-600" />
              <span>Real-Time Data Acquisition</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Automated Airfare Data Collection
            </h2>

            <p className="text-slate-600 text-base leading-relaxed">
              APEX-IND collects airfare observations for selected Indian
              domestic routes using Google Flights data accessed through
              the SerpApi API. Each observation records the flight,
              route, fare, departure date, booking window and scrape time.
            </p>

            <ul className="space-y-3 pt-2 text-sm text-slate-700 font-medium">

              <li className="flex items-start space-x-2.5">
                <CheckCircle2 className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
                <span>
                  Current MVP monitors 7 domestic airport corridors.
                </span>
              </li>

              <li className="flex items-start space-x-2.5">
                <CheckCircle2 className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
                <span>
                  Current collection uses T+1 and T+30 booking windows.
                </span>
              </li>

              <li className="flex items-start space-x-2.5">
                <CheckCircle2 className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
                <span>
                  Every successful observation is stored with a scrape timestamp.
                </span>
              </li>

            </ul>

          </div>

          <div className="lg:col-span-6">

            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white relative overflow-hidden">

              <div className="flex items-center justify-between pb-4 border-b border-slate-100">

                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-sky-600" />
                  <span className="font-bold text-xs uppercase text-slate-800 tracking-wider">
                    Acquisition Pipeline
                  </span>
                </div>

                <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                  SerpApi
                </span>

              </div>

              <div className="mt-4 space-y-3">

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">

                  <div className="flex items-center gap-3">

                    <div className="w-10 h-10 rounded-lg bg-sky-100 flex items-center justify-center">
                      <Server className="w-5 h-5 text-sky-600" />
                    </div>

                    <div>
                      <span className="font-bold text-sm text-slate-900 block">
                        Google Flights
                      </span>

                      <span className="text-xs text-slate-500">
                        Data source accessed through SerpApi
                      </span>
                    </div>

                  </div>

                </div>

                <div className="flex items-center justify-center">
                  <RefreshCw className="w-4 h-4 text-sky-500" />
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">

                  <div className="flex items-center gap-3">

                    <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                      <Database className="w-5 h-5 text-emerald-600" />
                    </div>

                    <div>
                      <span className="font-bold text-sm text-slate-900 block">
                        PostgreSQL / Supabase
                      </span>

                      <span className="text-xs text-slate-500">
                        flight_observations
                      </span>
                    </div>

                  </div>

                </div>

              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-medium">

                <span>6 Active Routes</span>

                <span className="text-emerald-600 font-bold flex items-center">
                  Data Pipeline Active
                  <CheckCircle2 className="w-3 h-3 ml-1" />
                </span>

              </div>

            </div>

          </div>

        </div>


        {/* =====================================================
            STEP 2 — CLEANING & VALIDATION
        ====================================================== */}

        <div
          id="deduplication"
          className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center"
        >

          <div className="lg:col-span-6 order-2 lg:order-1">

            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white">

              <div className="flex items-center justify-between mb-4">

                <span className="text-xs font-bold uppercase text-slate-800 tracking-wider flex items-center gap-1.5">
                  <Filter className="w-4 h-4 text-sky-600" />
                  Data Validation
                </span>

                <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">

                  <button
                    onClick={() => setActiveTabDedupe('cleaned')}
                    className={`px-3 py-1 rounded-md transition-all ${
                      activeTabDedupe === 'cleaned'
                        ? 'bg-sky-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Validated
                  </button>

                  <button
                    onClick={() => setActiveTabDedupe('raw')}
                    className={`px-3 py-1 rounded-md transition-all ${
                      activeTabDedupe === 'raw'
                        ? 'bg-sky-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Raw
                  </button>

                </div>

              </div>


              {activeTabDedupe === 'cleaned' ? (

                <div className="space-y-4">

                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">

                    <div className="flex items-center justify-between">

                      <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                        Observation Validation
                      </span>

                      <span className="text-xs font-mono font-bold text-emerald-700">
                        Active
                      </span>

                    </div>

                    <p className="text-xs text-emerald-800 mt-2">
                      Observations without a valid displayed fare are
                      excluded from insertion because the database requires
                      raw_price_displayed for observed fare records.
                    </p>

                  </div>


                  <div className="grid grid-cols-2 gap-3">

                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-center">

                      <span className="text-[11px] font-semibold text-slate-500 block">
                        Price Required
                      </span>

                      <span className="text-2xl font-extrabold text-slate-900 font-mono mt-1 block">
                        YES
                      </span>

                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-center">

                      <span className="text-[11px] font-semibold text-slate-500 block">
                        Sold-Out No-Price Rows
                      </span>

                      <span className="text-2xl font-extrabold text-sky-600 font-mono mt-1 block">
                        SKIP
                      </span>

                    </div>

                  </div>

                </div>

              ) : (

                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 space-y-2">

                  <div className="flex items-center justify-between text-rose-900 font-bold text-xs">

                    <span className="flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-rose-600" />
                      Raw Source Response
                    </span>

                    <span>Unvalidated</span>

                  </div>

                  <p className="text-xs text-rose-800">
                    Raw API responses may contain flights without a
                    usable price. These records are not inserted as
                    observed fare observations.
                  </p>

                </div>

              )}

            </div>

          </div>


          <div className="lg:col-span-6 space-y-5 text-left order-1 lg:order-2">

            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-blue-100 border border-blue-300 text-blue-800 text-xs font-bold uppercase tracking-wider">
              <Filter className="w-3.5 h-3.5 text-blue-600" />
              <span>Cleaning & Validation</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Validating and Normalizing Fare Observations
            </h2>

            <p className="text-slate-600 text-base leading-relaxed">
              The ingestion layer validates the fields required by the
              observation schema and removes unusable fare records.
              Sold-out results or flights without a displayed price are
              excluded instead of inserting artificial values.
            </p>

          </div>

        </div>


        {/* =====================================================
            STEP 3 — BOOKING WINDOWS
        ====================================================== */}

        <div
          id="booking-windows"
          className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center"
        >

          <div className="lg:col-span-6 space-y-5 text-left">

            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-sky-100 border border-sky-300 text-sky-800 text-xs font-bold uppercase tracking-wider">
              <Clock className="w-3.5 h-3.5 text-sky-600" />
              <span>Temporal Aggregation</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Standardizing Advance Booking Windows
            </h2>

            <p className="text-slate-600 text-base leading-relaxed">
              Airfare depends strongly on how far in advance a ticket is
              observed. The current MVP therefore separates observations
              into two fixed booking windows: T+1 and T+30.
            </p>

            <p className="text-slate-500 text-sm leading-relaxed">
              Additional windows such as T+7, T+15 and T+45 can be added
              later without changing the underlying observation model.
            </p>

          </div>


          <div className="lg:col-span-6">

            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white">

              <div className="flex items-center justify-between pb-3 border-b border-slate-100">

                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Current Booking Windows
                </span>

                <span className="text-xs font-semibold text-sky-600 font-mono">
                  MVP
                </span>

              </div>


              <div className="mt-4 grid grid-cols-2 gap-3">

                {['T+1', 'T+30'].map((window) => (

                  <button
                    key={window}
                    onClick={() => setSelectedWindow(window)}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      selectedWindow === window
                        ? 'bg-sky-600 text-white border-sky-600 shadow-md scale-[1.02]'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-sky-50'
                    }`}
                  >

                    <div className="flex items-center gap-2">

                      <Clock
                        className={`w-4 h-4 ${
                          selectedWindow === window
                            ? 'text-white'
                            : 'text-sky-600'
                        }`}
                      />

                      <span className="text-sm font-bold">
                        {window}
                      </span>

                    </div>

                    <span
                      className={`text-xs block mt-2 ${
                        selectedWindow === window
                          ? 'text-sky-100'
                          : 'text-slate-500'
                      }`}
                    >
                      {window === 'T+1'
                        ? 'Next-day departure'
                        : '30-day advance observation'}
                    </span>

                  </button>

                ))}

              </div>


              <div className="mt-4 p-3.5 rounded-xl bg-sky-50/80 border border-sky-200 text-xs text-slate-700 flex items-center justify-between">

                <div>

                  <span className="font-semibold text-slate-900 block">
                    Selected Window
                  </span>

                  <span className="text-slate-500">
                    Used by the current scraper
                  </span>

                </div>

                <span className="font-mono font-bold text-sky-700 px-2 py-1 bg-white rounded border border-sky-300">
                  {selectedWindow}
                </span>

              </div>

            </div>

          </div>

        </div>


        {/* =====================================================
            STEP 4 — GEKS METHODOLOGY
        ====================================================== */}

        <div
          id="geks-methodology"
          className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center"
        >

          <div className="lg:col-span-6 order-2 lg:order-1">

            <div className="p-6 rounded-2xl glass-panel border border-sky-500/30 shadow-2xl text-slate-100 space-y-5">

              <div className="flex items-center justify-between pb-3 border-b border-slate-700/60">

                <span className="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-sky-400" />
                  GEKS Methodology Demonstration
                </span>

                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-400/30">
                  Concept Demo
                </span>

              </div>


              {/* P1 */}
              <div className="space-y-3 text-xs">

                <div>

                  <div className="flex justify-between font-semibold text-slate-300 mb-1">

                    <span>
                      Period 1 Fare (P1)
                    </span>

                    <span className="font-mono text-sky-400 font-bold">
                      ₹{priceP1}
                    </span>

                  </div>

                  <input
                    type="range"
                    min="3000"
                    max="10000"
                    step="250"
                    value={priceP1}
                    onChange={(e) =>
                      setPriceP1(Number(e.target.value))
                    }
                    className="w-full accent-sky-500"
                  />

                </div>


                {/* P2 */}
                <div>

                  <div className="flex justify-between font-semibold text-slate-300 mb-1">

                    <span>
                      Period 2 Fare (P2)
                    </span>

                    <span className="font-mono text-rose-400 font-bold">
                      ₹{priceP2}
                    </span>

                  </div>

                  <input
                    type="range"
                    min="3000"
                    max="12000"
                    step="250"
                    value={priceP2}
                    onChange={(e) =>
                      setPriceP2(Number(e.target.value))
                    }
                    className="w-full accent-rose-500"
                  />

                </div>


                {/* P3 */}
                <div>

                  <div className="flex justify-between font-semibold text-slate-300 mb-1">

                    <span>
                      Period 3 Fare (P3)
                    </span>

                    <span className="font-mono text-emerald-400 font-bold">
                      ₹{priceP3}
                    </span>

                  </div>

                  <input
                    type="range"
                    min="3000"
                    max="10000"
                    step="250"
                    value={priceP3}
                    onChange={(e) =>
                      setPriceP3(Number(e.target.value))
                    }
                    className="w-full accent-emerald-500"
                  />

                </div>

              </div>


              {/* GEKS Result */}
              <div className="pt-2">

                <div className="p-4 rounded-xl bg-sky-950/60 border border-sky-400/40 space-y-2">

                  <span className="text-sky-300 block font-semibold">
                    Direct Price Comparison
                  </span>

                  <span className="text-2xl font-extrabold text-emerald-400 font-mono block">
                    {geksIndex}
                  </span>

                  <span className="text-[10px] text-emerald-400/80 block">
                    P3 relative to P1, with P1 = 100
                  </span>

                </div>

              </div>


              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700 text-[11px] text-slate-400 leading-relaxed">
                This interactive panel illustrates the idea of
                transitive price comparison. It is a methodology
                demonstration and is not the production index returned
                by the current backend.
              </div>

            </div>

          </div>


          <div className="lg:col-span-6 space-y-5 text-left order-1 lg:order-2">

            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-sky-100 border border-sky-300 text-sky-800 text-xs font-bold uppercase tracking-wider">
              <Calculator className="w-3.5 h-3.5 text-sky-600" />
              <span>Index Methodology</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Multilateral GEKS for Airfare Price Measurement
            </h2>

            <p className="text-slate-600 text-base leading-relaxed">
              The planned APEX-IND methodology uses a multilateral GEKS
              framework to reduce chain drift and improve transitivity
              when comparing prices across multiple periods.
            </p>

            <p className="text-slate-500 text-sm leading-relaxed">
              The current backend is still in the data-acquisition and
              basic index stage. The production GEKS calculation will be
              connected to the statistical/index layer after the scraper
              pipeline is finalized.
            </p>

          </div>

        </div>


        {/* =====================================================
            STEP 5 — MOSPI
        ====================================================== */}

        <div
          id="mospi-calibration"
          className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center"
        >

          <div className="lg:col-span-6 space-y-5 text-left">

            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-blue-100 border border-blue-300 text-blue-800 text-xs font-bold uppercase tracking-wider">
              <LineChart className="w-3.5 h-3.5 text-blue-600" />
              <span>MoSPI Comparison</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Comparing the Airfare Signal with Official CPI Data
            </h2>

            <p className="text-slate-600 text-base leading-relaxed">
              APEX-IND is intended to provide a higher-frequency airfare
              signal that can eventually be compared with official
              MoSPI CPI transport statistics.
            </p>

            <p className="text-slate-500 text-sm leading-relaxed">
              MoSPI CPI data is published at a different frequency and
              geographic/statistical level, so the final comparison
              requires compatible aggregation and calibration.
            </p>

          </div>


          <div className="lg:col-span-6">

            <div className="light-section-card p-6 rounded-2xl border border-sky-200 shadow-xl bg-white space-y-4">

              <div className="flex items-center justify-between pb-3 border-b border-slate-100">

                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Comparison Layer
                </span>

                <span className="text-xs font-semibold text-slate-500 font-mono">
                  Planned
                </span>

              </div>


              <div className="space-y-3">

                <div className="p-4 rounded-xl bg-sky-50 border border-sky-200">

                  <div className="flex items-center gap-3">

                    <div className="w-9 h-9 rounded-lg bg-sky-100 flex items-center justify-center">
                      <BarChart3 className="w-4 h-4 text-sky-600" />
                    </div>

                    <div>

                      <span className="text-xs font-bold text-slate-900 block">
                        APEX-IND Airfare Observations
                      </span>

                      <span className="text-[11px] text-slate-500">
                        High-frequency route-level data
                      </span>

                    </div>

                  </div>

                </div>


                <div className="flex items-center justify-center">
                  <RefreshCw className="w-4 h-4 text-slate-400" />
                </div>


                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">

                  <div className="flex items-center gap-3">

                    <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center">
                      <LineChart className="w-4 h-4 text-blue-600" />
                    </div>

                    <div>

                      <span className="text-xs font-bold text-slate-900 block">
                        MoSPI CPI Transport
                      </span>

                      <span className="text-[11px] text-slate-500">
                        Official lower-frequency benchmark
                      </span>

                    </div>

                  </div>

                </div>

              </div>


              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 font-medium">

                <div className="flex items-start gap-2">

                  <Plane className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />

                  <span>
                    The final comparison will be added after the
                    route-level airfare index and compatible MoSPI
                    aggregation are implemented.
                  </span>

                </div>

              </div>

            </div>

          </div>

        </div>

      </div>

    </section>
  );
}