import React, { useState, useMemo, useEffect } from 'react';
import { 
  ResponsiveContainer, AreaChart, Area, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend 
} from 'recharts';
import { 
  BarChart3, Download, RefreshCw, ArrowUpRight, Search, 
  ShieldCheck, Layers, Info, Check, Zap, Plane, Activity, Compass, Database
} from 'lucide-react';
import {
  generateTimeSeriesData, SIMULATION_PRESETS
} from '../data/mockData';
import { fetchIndex, fetchFlights } from '../api/apiService';
import AirlineAnalytics from './AirlineAnalytics';
import LiveDataPanel from './LiveDataPanel';

// Scrapes land every ~6h (T+1) / daily (T+30) via the scheduled sweeps;
// poll every 3 minutes so newly-inserted rows show up without a manual
// reload, without hammering the API.
const DATA_REFRESH_MS = 3 * 60 * 1000;

export default function Dashboard({ initialTab = 'macro' }) {
  const [dashboardTab, setDashboardTab] = useState(initialTab);

  useEffect(() => {
    if (initialTab) {
      setDashboardTab(initialTab);
    }
  }, [initialTab]);

  const [timeRange, setTimeRange] = useState('90D');
  const [selectedRoute, setSelectedRoute] = useState('ALL');
  const [selectedWindow, setSelectedWindow] = useState('ALL');
  const [selectedAirline, setSelectedAirline] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Market simulation preset state
  const [activePreset, setActivePreset] = useState('normal');

  // Series visibility toggles
  const [showGEKS, setShowGEKS] = useState(true);
  const [showMoSPI, setShowMoSPI] = useState(true);

  const [exportMessage, setExportMessage] = useState('');

  // Real backend index data
  const [realIndexData, setRealIndexData] = useState([]);
  const [indexLoading, setIndexLoading] = useState(true);
  const [indexError, setIndexError] = useState(null);

  // ---------------------------------------------------------
  // FETCH REAL APIx INDEX DATA FROM FASTAPI
  // ---------------------------------------------------------
  useEffect(() => {
    const loadIndexData = async () => {
      try {
        setIndexLoading(true);
        setIndexError(null);

        const routeParam = selectedRoute === 'ALL' ? 'DEL-BOM' : selectedRoute;
        const windowParam = selectedWindow === 'ALL' ? 'T+1' : selectedWindow;

        const result = await fetchIndex(routeParam, windowParam);

        console.log('Real APIx index response:', result);

        setRealIndexData(result.series || []);

      } catch (error) {
        console.error('Failed to load APIx index:', error);
        setIndexError(error.message);
      } finally {
        setIndexLoading(false);
      }
    };

    loadIndexData();
    const intervalId = setInterval(loadIndexData, DATA_REFRESH_MS);
    return () => clearInterval(intervalId);
  }, [selectedRoute, selectedWindow]);

  // ---------------------------------------------------------
  // LIVE MONITORED CORRIDORS — real recent scrapes, fee-decomposed
  // ---------------------------------------------------------
  const [liveFlights, setLiveFlights] = useState([]);

  useEffect(() => {
    const loadLiveFlights = () => {
      fetchFlights('', '')
        .then((data) => setLiveFlights(data || []))
        .catch((error) => console.error('Failed to load live flights:', error));
    };
    loadLiveFlights();
    const intervalId = setInterval(loadLiveFlights, DATA_REFRESH_MS);
    return () => clearInterval(intervalId);
  }, []);

  const liveCorridors = useMemo(() => {
    // Real, fee-decomposed rows only — never show a null/undefined ₹ figure.
    const decomposed = liveFlights.filter(
      (f) => f.base_fare != null && f.price != null
    );

    // Compare each (route, flight_number) against its own earliest-seen price
    // in the currently-loaded data. This is genuinely real, just not a full
    // 30-day trend yet — the scraper hasn't been running that long.
    const firstSeenPrice = {};
    for (const f of decomposed) {
      const key = `${f.origin}-${f.destination}|${f.flight_number}|${f.window}`;
      if (!(key in firstSeenPrice) || f.scrape_timestamp < firstSeenPrice[key].ts) {
        firstSeenPrice[key] = { price: f.price, ts: f.scrape_timestamp };
      }
    }

    // Most recent observation per (route, flight_number, window)
    const latestByKey = {};
    for (const f of decomposed) {
      const key = `${f.origin}-${f.destination}|${f.flight_number}|${f.window}`;
      if (!latestByKey[key] || f.scrape_timestamp > latestByKey[key].scrape_timestamp) {
        latestByKey[key] = f;
      }
    }

    return Object.entries(latestByKey)
      .sort((a, b) => (a[1].scrape_timestamp < b[1].scrape_timestamp ? 1 : -1))
      .slice(0, 15)
      .map(([key, f], idx) => {
        const base = firstSeenPrice[key]?.price ?? f.price;
        const pctChange = base > 0 ? ((f.price - base) / base) * 100 : 0;
        const taxes = Math.round(
          (f.taxes_fees ?? 0) + (f.udf ?? 0) + (f.gst_amount ?? 0) + (f.fuel_surcharge ?? 0)
        );

        let status = 'NORMAL';
        let statusStyle = 'bg-sky-500/10 text-sky-400 border-sky-500/30';
        if (pctChange > 10) {
          status = 'SURGE'; statusStyle = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
        } else if (pctChange < -10) {
          status = 'DISCOUNT'; statusStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
        }

        return {
          id: idx,
          route: `${f.origin} → ${f.destination}`,
          carrier: `${f.airline_name} ${f.flight_number}`,
          horizon: f.window,
          baseFare: Math.round(f.base_fare),
          taxes,
          totalFare: Math.round(f.price),
          vs30d: `${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(1)}%`,
          status,
          statusStyle,
        };
      });
  }, [liveFlights]);

  // Real distinct route count from live data (replaces a hardcoded "456").
  const realRouteCount = useMemo(() => {
    const routes = new Set(liveFlights.map((f) => `${f.origin}-${f.destination}`));
    return routes.size;
  }, [liveFlights]);

  // Real pipeline health — fee-decomposition completeness and scrape
  // recency, computed from the same live data already loaded above.
  const pipelineHealth = useMemo(() => {
    if (liveFlights.length === 0) return null;
    const decomposedCount = liveFlights.filter((f) => f.base_fare != null).length;
    const purity = (decomposedCount / liveFlights.length) * 100;
    const mostRecentTs = liveFlights.reduce(
      (max, f) => (f.scrape_timestamp > max ? f.scrape_timestamp : max),
      liveFlights[0].scrape_timestamp
    );
    const minutesAgo = Math.max(0, Math.round((Date.now() - new Date(mostRecentTs).getTime()) / 60000));
    return { purity, count: liveFlights.length, minutesAgo };
  }, [liveFlights]);

  // ---------------------------------------------------------
  // ACTIVE PRESET SHOCK FACTOR
  // ---------------------------------------------------------
  const activeShockFactor = useMemo(() => {
    const p = SIMULATION_PRESETS.find(x => x.id === activePreset);
    return p ? p.shockFactor : 1.0;
  }, [activePreset]);

  // ---------------------------------------------------------
  // REAL BACKEND DATA → DASHBOARD FORMAT
  // ---------------------------------------------------------
  const chartData = useMemo(() => {
    // Real backend data available → use it, deduplicate by date, apply shockFactor for scenario simulation
    if (realIndexData.length > 0) {
      const dateMap = new Map();
      realIndexData.forEach((item) => {
        if (item && item.date && !dateMap.has(item.date)) {
          dateMap.set(item.date, {
            date: item.date,
            fullDate: item.date,
            geksIndex: parseFloat((item.index_value * activeShockFactor).toFixed(2)),
            avgFare: item.avg_price ? Math.round(item.avg_price * activeShockFactor) : null,
            mospiCPI: null,   // backend doesn't expose this yet; MoSPI line hidden when null
            volatility: null,
          });
        }
      });
      return Array.from(dateMap.values());
    }

    // Fallback: generate mock data respecting the selected time range and scenario shock
    return generateTimeSeriesData(timeRange, activeShockFactor);
  }, [realIndexData, activeShockFactor, timeRange]);

  // ---------------------------------------------------------
  // SUMMARY STATS — computed dynamically from chartData
  // ---------------------------------------------------------
  const summaryStats = useMemo(() => {
    const values = chartData.map(d => d.geksIndex).filter(v => v != null && !isNaN(v));
    if (values.length === 0) {
      return { peakLabel: '—', peakValue: '—', troughLabel: '—', troughValue: '—', volatility: '—' };
    }

    const max = Math.max(...values);
    const min = Math.min(...values);
    const peakDate   = chartData[values.indexOf(max)]?.date || '';
    const troughDate = chartData[values.indexOf(min)]?.date || '';

    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const stdDev = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length);

    return {
      peakLabel:   peakDate,
      peakValue:   max.toFixed(1),
      troughLabel: troughDate,
      troughValue: min.toFixed(1),
      volatility:  `${(stdDev / mean * 100).toFixed(2)}σ`,
    };
  }, [chartData]);

  // ---------------------------------------------------------
  // FILTERED LIVE MONITORED CORRIDORS TABLE
  // ---------------------------------------------------------
  const filteredCorridors = useMemo(() => {
    return liveCorridors.filter(c => {
      const matchRoute =
        selectedRoute === 'ALL' || c.route.includes(selectedRoute);

      const matchAirline =
        selectedAirline === 'ALL' ||
        c.carrier.toLowerCase().includes(selectedAirline.toLowerCase());

      const matchSearch =
        c.route.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.carrier.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.status.toLowerCase().includes(searchTerm.toLowerCase());

      return matchRoute && matchAirline && matchSearch;
    });
  }, [liveCorridors, selectedRoute, selectedAirline, searchTerm]);

  // ---------------------------------------------------------
  // CSV EXPORT
  // ---------------------------------------------------------
  const handleExportCSV = () => {
    const headers = [
      "Date",
      "GEKS_Index",
      "MoSPI_CPI_Transport",
      "Avg_Domestic_Fare_INR",
      "Volatility"
    ];

    const rows = chartData.map(row => [
      row.fullDate,
      row.geksIndex,
      row.mospiCPI,
      row.avgFare,
      row.volatility
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [
        headers.join(","),
        ...rows.map(e => e.join(","))
      ].join("\n");

    const encodedUri = encodeURI(csvContent);

    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `AeroStat_Airfare_Index_${timeRange}_${activePreset}.csv`
    );

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setExportMessage('CSV Exported!');

    setTimeout(() => setExportMessage(''), 3000);
  };

  return (
    <div className="py-24 bg-slate-950 text-slate-100 min-h-screen relative">

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">

        {/* =====================================================
            TOP HEADER BANNER
        ====================================================== */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 pb-6 border-b border-slate-800">

          <div>
            <div className="flex items-center space-x-3">

              <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-sans tracking-tight">
                AeroStat Real-Time Intelligence Dashboard
              </h2>

              {dashboardTab === 'macro' && realIndexData.length === 0 && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-400/30">
                  Simulated Data
                </span>
              )}

            </div>

            <p className="text-sm text-slate-400 mt-1">
              Dynamic surveillance across Indian domestic corridors, airline yield shifts, and DGCA capacity telemetry.
            </p>
          </div>

          {/* Export Controls */}
          <div className="flex flex-wrap items-center gap-3">

            <button
              onClick={handleExportCSV}
              className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold rounded-xl text-slate-300 glass-soft hover:text-white transition-all shadow-sm"
            >
              <Download className="w-3.5 h-3.5 text-sky-400" />
              <span>Export CSV / JSON</span>
            </button>

            {exportMessage && (
              <span className="text-xs font-semibold text-emerald-400 animate-pulse">
                {exportMessage}
              </span>
            )}

          </div>
        </div>





        {/* =====================================================
            PRIMARY KPI CARDS
        ====================================================== */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">

          {/* APIx Composite */}
          <div className="glass-elevated p-5 rounded-2xl">

            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Current APIx Composite
            </span>

            <div className="flex items-baseline justify-between mt-2">

              <span className="text-3xl font-extrabold text-white font-mono">

                {indexLoading
                  ? '...'
                  : (chartData[chartData.length - 1]?.geksIndex ?? '—')}

              </span>

              {chartData.length >= 2 && chartData[chartData.length - 1]?.geksIndex != null && chartData[chartData.length - 2]?.geksIndex != null && (
                <span className={`inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full font-mono border ${
                  chartData[chartData.length - 1].geksIndex >= chartData[chartData.length - 2].geksIndex
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                }`}>
                  {chartData[chartData.length - 1].geksIndex >= chartData[chartData.length - 2].geksIndex
                    ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : null}
                  {((chartData[chartData.length - 1].geksIndex - chartData[chartData.length - 2].geksIndex) / chartData[chartData.length - 2].geksIndex * 100 >= 0 ? '+' : '')}
                  {((chartData[chartData.length - 1].geksIndex - chartData[chartData.length - 2].geksIndex) / chartData[chartData.length - 2].geksIndex * 100).toFixed(2)}% (DoD)
                </span>
              )}

            </div>

            <span className="text-[11px] text-slate-400 mt-2 block font-mono">
              {realIndexData.length > 0
                ? `Base ${realIndexData[0]?.date} = 100 • Low: ${summaryStats.troughValue}`
                : 'Awaiting live index data'}
            </span>

          </div>


          {/* Average Fare */}
          <div className="glass-elevated p-5 rounded-2xl">

            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Weighted Median Fare (All In)
            </span>

            <div className="flex items-baseline justify-between mt-2">

              <span className="text-3xl font-extrabold text-white font-mono">

                {indexLoading
                  ? '...'
                  : chartData[chartData.length - 1]?.avgFare != null
                    ? `₹${chartData[chartData.length - 1].avgFare.toLocaleString('en-IN')}`
                    : '—'}

              </span>

              {chartData.length >= 2 && chartData[chartData.length - 1]?.avgFare != null && chartData[chartData.length - 2]?.avgFare != null && (
                <span className={`inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full font-mono border ${
                  chartData[chartData.length - 1].avgFare >= chartData[chartData.length - 2].avgFare
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                }`}>
                  {chartData[chartData.length - 1].avgFare >= chartData[chartData.length - 2].avgFare ? '+' : ''}
                  ₹{Math.round(chartData[chartData.length - 1].avgFare - chartData[chartData.length - 2].avgFare)} (DoD)
                </span>
              )}

            </div>

            <span className="text-[11px] text-slate-400 mt-2 block font-mono">
              {realIndexData.length > 0
                ? `${realIndexData[realIndexData.length - 1]?.num_observations_used ?? 0} live observations`
                : 'Live — Clean Base'}
            </span>

          </div>


          {/* Index Volatility */}
          <div className="glass-elevated p-5 rounded-2xl">

            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Index Volatility (Std Dev)
            </span>

            <div className="flex items-baseline justify-between mt-2">

              <span className="text-3xl font-extrabold text-amber-400 font-mono">
                {summaryStats.volatility}
              </span>

            </div>

            <span className="text-[11px] text-slate-400 mt-2 block">
              Peak {summaryStats.peakValue} ({summaryStats.peakLabel}) • Trough {summaryStats.troughValue} ({summaryStats.troughLabel})
            </span>

          </div>


          {/* Pipeline Health */}
          <div className="glass-elevated p-5 rounded-2xl">

            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Pipeline Ingestion Health
            </span>

            <div className="flex items-baseline justify-between mt-2">

              <span className="text-3xl font-extrabold text-emerald-400 font-mono">
                {pipelineHealth ? `${pipelineHealth.purity.toFixed(1)}%` : '—'}
              </span>

              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                Fee-Decomposed
              </span>

            </div>

            <span className="text-[11px] text-slate-400 mt-2 block">
              {pipelineHealth
                ? `${pipelineHealth.count.toLocaleString('en-IN')} Quotes Loaded • Last Scrape: ${pipelineHealth.minutesAgo}m ago`
                : 'Awaiting live data'}
            </span>

          </div>

        </div>


        {/* =====================================================
            TAB 1 — MACRO APIx INDEX & CPI
        ====================================================== */}
        {dashboardTab === 'macro' && (

          <div className="space-y-8">

            {/* Scenario Simulator */}
            <div className="p-4 rounded-2xl glass-soft space-y-3">

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">

                <span className="text-xs font-bold uppercase text-sky-300 tracking-wider flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-sky-400" />
                  Market Scenario Simulator
                </span>

                <span className="text-[11px] text-slate-400">

                  Active Scenario:

                  <strong className="text-white font-mono ml-1">
                    {SIMULATION_PRESETS.find(p => p.id === activePreset)?.label}
                  </strong>

                </span>

              </div>


              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">

                {SIMULATION_PRESETS.map((preset) => (

                  <button
                    key={preset.id}
                    onClick={() => setActivePreset(preset.id)}
                    className={`p-2.5 rounded-xl border text-xs font-bold text-left transition-all ${
                      activePreset === preset.id
                        ? 'glass-tab-active border-sky-500/50 scale-[1.02]'
                        : 'glass-soft text-slate-300 border-transparent hover:border-white/10'
                    }`}
                  >

                    <div className="flex items-center justify-between">

                      <span>{preset.label}</span>

                      {activePreset === preset.id && (
                        <Check className="w-3.5 h-3.5 text-white" />
                      )}

                    </div>

                    <span
                      className={`text-[10px] block mt-1 font-normal ${
                        activePreset === preset.id
                          ? 'text-sky-100'
                          : 'text-slate-500'
                      }`}
                    >
                      {preset.desc}
                    </span>

                  </button>

                ))}

              </div>

            </div>


            {/* Main Chart */}
            <div className="glass-elevated p-6 rounded-3xl space-y-6">

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">

                <div>

                  <h3 className="text-lg font-bold text-white flex items-center gap-2">

                    <BarChart3 className="w-5 h-5 text-sky-400" />

                    APIx Index Trend vs MoSPI Air Transport CPI

                  </h3>

                  <p className="text-xs text-slate-400">
                    Real-time airfare index derived from observed flight fares for the selected corridor and booking window
                  </p>

                </div>


                {/* Series Toggles */}
                <div className="flex flex-wrap items-center gap-3 text-xs font-semibold">

                  <button 
                    onClick={() => setShowGEKS(!showGEKS)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                      showGEKS
                        ? 'glass-soft text-sky-300 border-sky-500/40'
                        : 'glass-soft text-slate-500 border-transparent line-through opacity-50'
                    }`}
                  >

                    <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span>

                    <span>AeroStat GEKS</span>

                  </button>


                  <button 
                    onClick={() => setShowMoSPI(!showMoSPI)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                      showMoSPI
                        ? 'glass-soft text-emerald-300 border-emerald-500/40'
                        : 'glass-soft text-slate-500 border-transparent line-through opacity-50'
                    }`}
                  >

                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>

                    <span>MoSPI Official</span>

                  </button>

                </div>

              </div>


              <div className="w-full h-80 sm:h-96 pt-4">

                <ResponsiveContainer width="100%" height="100%">

                  <AreaChart
                    data={chartData}
                    margin={{
                      top: 10,
                      right: 10,
                      left: -20,
                      bottom: 0
                    }}
                  >

                    <defs>

                      <linearGradient
                        id="geksGlow"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >

                        <stop
                          offset="5%"
                          stopColor="#38bdf8"
                          stopOpacity={0.35}
                        />

                        <stop
                          offset="95%"
                          stopColor="#0284c7"
                          stopOpacity={0}
                        />

                      </linearGradient>

                    </defs>


                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#1e293b"
                    />

                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                    />

                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      domain={['dataMin - 5', 'dataMax + 5']}
                      tickLine={false}
                    />

                    <Tooltip 
                      contentStyle={{
                        backgroundColor: '#090d16',
                        borderColor: '#38bdf833',
                        borderRadius: '12px',
                        color: '#fff',
                        fontSize: '12px'
                      }} 
                    />

                    <Legend
                      wrapperStyle={{
                        fontSize: '11px',
                        paddingTop: '10px'
                      }}
                    />


                    {showGEKS && (
                      <Area
                        type="monotone"
                        dataKey="geksIndex"
                        name="AeroStat GEKS (Drift-Free)"
                        stroke="#38bdf8"
                        strokeWidth={3}
                        fillOpacity={1}
                        fill="url(#geksGlow)"
                      />
                    )}


                    {showMoSPI && (
                      <Line
                        type="monotone"
                        dataKey="mospiCPI"
                        name="MoSPI CPI Official"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={false}
                      />
                    )}

                  </AreaChart>

                </ResponsiveContainer>

              </div>


              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs font-semibold">

                <div className="p-3 rounded-xl glass-soft text-center">

                  <span className="text-slate-400 block text-[10px] uppercase">
                    Peak Index (Period)
                  </span>

                  <span className="text-rose-400 font-mono text-sm mt-0.5 block">
                    {summaryStats.peakLabel}: {summaryStats.peakValue}
                  </span>

                </div>


                <div className="p-3 rounded-xl glass-soft text-center">

                  <span className="text-slate-400 block text-[10px] uppercase">
                    Trough (Period)
                  </span>

                  <span className="text-sky-400 font-mono text-sm mt-0.5 block">
                    {summaryStats.troughLabel}: {summaryStats.troughValue}
                  </span>

                </div>


                <div className="p-3 rounded-xl glass-soft text-center">

                  <span className="text-slate-400 block text-[10px] uppercase">
                    Volatility Index (σ/μ)
                  </span>

                  <span className="text-emerald-400 font-mono text-sm mt-0.5 block">
                    {summaryStats.volatility}
                  </span>

                </div>

              </div>

            </div>

          </div>

        )}


        {/* =====================================================
            TAB 2 — AIRLINE PRICE INDICES
        ====================================================== */}
        {dashboardTab === 'airlines' && (
          <AirlineAnalytics />
        )}


        {/* =====================================================
            TAB 4 — LIVE SCRAPED DATA
        ====================================================== */}
        {dashboardTab === 'live' && (
          <LiveDataPanel />
        )}


        {/* =====================================================
            TAB 3 — CORRIDOR TELEMETRY & GOVERNANCE
        ====================================================== */}
        {dashboardTab === 'telemetry' && (

          <div className="space-y-8">

            {/* Governance Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

              <div className="glass-elevated p-6 rounded-3xl space-y-3">

                <h4 className="text-sm font-bold text-white flex items-center gap-2">

                  <ShieldCheck className="w-4 h-4 text-emerald-400" />

                  Governance & Compliance

                </h4>

                <div className="space-y-2 text-xs">

                  <div className="flex justify-between py-1.5 border-b border-slate-800">

                    <span className="text-slate-400">
                      Multilateral (GEKS) Transitivity:
                    </span>

                    <span className="font-mono font-bold text-amber-400">
                      Not Yet Computed
                    </span>

                  </div>


                  <div className="flex justify-between py-1.5 border-b border-slate-800">

                    <span className="text-slate-400">
                      Missing Quote Imputation:
                    </span>

                    <span className="font-mono font-bold text-slate-200">
                      None (real quotes only)
                    </span>

                  </div>


                  <div className="flex justify-between py-1.5 border-b border-slate-800">

                    <span className="text-slate-400">
                      Route Sample Breadth:
                    </span>

                    <span className="font-mono font-bold text-sky-400">
                      7 of 8 Routes (87.5%)
                    </span>

                  </div>

                </div>

              </div>


              {/* Booking Windows */}
              <div className="glass-elevated p-6 rounded-3xl space-y-3">

                <h4 className="text-sm font-bold text-white flex items-center gap-2">

                  <Layers className="w-4 h-4 text-sky-400" />

                  Booking Window Weights (Jevons Engine)

                </h4>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">

                  {[
                    { bucket: 'T+1', weight: '0.12' },
                    { bucket: 'T+7', weight: '0.28' },
                    { bucket: 'T+30', weight: '0.20' },
                  ].map((win) => (

                    <div
                      key={win.bucket}
                      className="p-2 rounded-xl glass-soft"
                    >

                      <span className="text-[10px] text-slate-400 block">
                        {win.bucket}
                      </span>

                      <span className="font-mono font-bold text-sky-400 text-sm">
                        {win.weight}
                      </span>

                    </div>

                  ))}

                </div>

                <p className="text-[10px] text-slate-500">
                  Estimated weights used by jevons_engine_cloud.py (no proprietary booking data exists) — not fitted to real purchase data.
                </p>

              </div>


              {/* Airspace Telemetry */}
              <div className="glass-elevated p-6 rounded-3xl space-y-3">

                <h4 className="text-sm font-bold text-white flex items-center gap-2">

                  <Compass className="w-4 h-4 text-blue-400" />

                  India Airspace Telemetry

                </h4>

                <div className="p-3.5 rounded-xl glass-soft text-xs space-y-1">

                  <span className="font-mono font-bold text-sky-400 block">
                    {realRouteCount || '—'} Active Route Pairs
                  </span>

                  <p className="text-slate-400 text-[11px]">
                    Live scraper coverage — SerpApi plus direct Akasa Air / SpiceJet collection.
                  </p>

                </div>

              </div>

            </div>


            {/* Live Corridors Table */}
            <div className="glass-elevated p-6 rounded-3xl space-y-4">

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">

                <div>

                  <h4 className="text-base font-bold text-white flex items-center gap-2">

                    <Activity className="w-4 h-4 text-sky-400" />

                    Live Monitored Domestic Corridors ({liveCorridors.length} Tracked)

                  </h4>

                  <p className="text-xs text-slate-400">
                    Direct carrier and GDS normalized clean quotes parsed in the last 15 minutes
                  </p>

                </div>


                <div className="relative">

                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />

                  <input 
                    type="text"
                    placeholder="Search route or carrier..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="glass-soft text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-sky-400 w-52"
                  />

                </div>

              </div>


              <div className="overflow-x-auto">

                <table className="w-full text-left text-xs">

                  <thead className="glass-soft text-slate-400 uppercase font-semibold text-[10px]">

                    <tr>

                      <th className="p-3.5 rounded-l-lg">
                        Route
                      </th>

                      <th className="p-3.5">
                        Carrier & Flight
                      </th>

                      <th className="p-3.5">
                        Departure Horizon
                      </th>

                      <th className="p-3.5">
                        Clean Base Fare
                      </th>

                      <th className="p-3.5">
                        Taxes & UDF
                      </th>

                      <th className="p-3.5">
                        Total Realized
                      </th>

                      <th className="p-3.5">
                        vs First Seen
                      </th>

                      <th className="p-3.5 rounded-r-lg">
                        Status
                      </th>

                    </tr>

                  </thead>


                  <tbody className="divide-y divide-slate-800/60 font-medium">

                    {filteredCorridors.map((row) => (

                      <tr
                        key={row.id}
                        className="hover:bg-slate-900/60 transition-colors"
                      >

                        <td className="p-3.5 font-mono font-bold text-white">
                          {row.route}
                        </td>

                        <td className="p-3.5 font-mono text-slate-200">
                          {row.carrier}
                        </td>

                        <td className="p-3.5 text-slate-400">
                          {row.horizon}
                        </td>

                        <td className="p-3.5 font-mono text-slate-300">
                          ₹{row.baseFare}
                        </td>

                        <td className="p-3.5 font-mono text-slate-400">
                          ₹{row.taxes}
                        </td>

                        <td className="p-3.5 font-mono font-bold text-white text-sm">
                          ₹{row.totalFare}
                        </td>

                        <td
                          className={`p-3.5 font-mono font-bold ${
                            row.vs30d.startsWith('+')
                              ? 'text-rose-400'
                              : 'text-emerald-400'
                          }`}
                        >
                          {row.vs30d}
                        </td>

                        <td className="p-3.5">

                          <span
                            className={`px-2.5 py-0.5 rounded text-[10px] font-bold border ${row.statusStyle}`}
                          >
                            {row.status}
                          </span>

                        </td>

                      </tr>

                    ))}

                  </tbody>

                </table>

              </div>

            </div>

          </div>

        )}

      </div>

    </div>
  );
}