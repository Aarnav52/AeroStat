import React, { useState, useMemo } from 'react';
import { 
  ResponsiveContainer, AreaChart, Area, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend 
} from 'recharts';
import { 
  BarChart3, Download, RefreshCw, ArrowUpRight, Search, 
  ShieldCheck, Layers, Info, Check, Zap, Plane, Activity, Compass, Database
} from 'lucide-react';
import { 
  generateTimeSeriesData, TOP_ROUTES_DATA, AIRLINE_BREAKDOWN, 
  BOOKING_WINDOWS, LIVE_MONITORED_CORRIDORS, GOVERNANCE_STATS, SIMULATION_PRESETS
} from '../data/mockData';
import AirlineAnalytics from './AirlineAnalytics';
import LiveDataPanel from './LiveDataPanel';

export default function Dashboard() {
  const [dashboardTab, setDashboardTab] = useState('macro'); // 'macro', 'airlines', 'telemetry'
  const [timeRange, setTimeRange] = useState('90D');
  const [selectedRoute, setSelectedRoute] = useState('ALL');
  const [selectedWindow, setSelectedWindow] = useState('ALL');
  const [selectedAirline, setSelectedAirline] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Market simulation preset state
  const [activePreset, setActivePreset] = useState('normal');

  // Series visibility toggles
  const [showGEKS, setShowGEKS] = useState(true);
  const [showLaspeyres, setShowLaspeyres] = useState(true);
  const [showMoSPI, setShowMoSPI] = useState(true);

  const [exportMessage, setExportMessage] = useState('');

  // Active preset shock factor
  const activeShockFactor = useMemo(() => {
    const p = SIMULATION_PRESETS.find(x => x.id === activePreset);
    return p ? p.shockFactor : 1.0;
  }, [activePreset]);

  // Dynamic time series dataset
  const chartData = useMemo(() => {
    return generateTimeSeriesData(timeRange, activeShockFactor);
  }, [timeRange, activeShockFactor]);

  // Filtered live monitored corridors table
  const filteredCorridors = useMemo(() => {
    return LIVE_MONITORED_CORRIDORS.filter(c => {
      const matchRoute = selectedRoute === 'ALL' || c.route.includes(selectedRoute);
      const matchAirline = selectedAirline === 'ALL' || c.carrier.toLowerCase().includes(selectedAirline.toLowerCase());
      const matchSearch = c.route.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          c.carrier.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          c.status.toLowerCase().includes(searchTerm.toLowerCase());
      return matchRoute && matchAirline && matchSearch;
    });
  }, [selectedRoute, selectedAirline, searchTerm]);

  // CSV Export feature
  const handleExportCSV = () => {
    const headers = ["Date", "GEKS_Index", "Laspeyres_Index", "MoSPI_CPI_Transport", "Avg_Domestic_Fare_INR", "Volatility"];
    const rows = chartData.map(row => [
      row.fullDate, row.geksIndex, row.laspeyresIndex, row.mospiCPI, row.avgFare, row.volatility
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `APEX_IND_Airfare_Index_${timeRange}_${activePreset}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setExportMessage('CSV Exported!');
    setTimeout(() => setExportMessage(''), 3000);
  };

  return (
    <div className="py-24 bg-slate-950 text-slate-100 min-h-screen relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Top Header Banner */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-sans tracking-tight">
                APEX-IND Real-Time Intelligence Dashboard
              </h2>
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
                SYSTEM ONLINE
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Dynamic surveillance across Indian domestic corridors, airline yield shifts, and DGCA capacity telemetry.
            </p>
          </div>

          {/* Export & Preset Controls */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleExportCSV}
              className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold rounded-xl text-slate-200 bg-slate-900 border border-slate-700 hover:bg-slate-800 transition-all shadow-sm"
            >
              <Download className="w-3.5 h-3.5 text-sky-400" />
              <span>Export CSV / JSON</span>
            </button>

            {exportMessage && (
              <span className="text-xs font-semibold text-emerald-400 animate-pulse">{exportMessage}</span>
            )}
          </div>
        </div>

        {/* Dashboard Navigation Sub-Tabs */}
        <div className="flex border-b border-slate-800/80 space-x-6 text-sm font-bold">
          <button
            onClick={() => setDashboardTab('macro')}
            className={`pb-3 flex items-center space-x-2 transition-all border-b-2 ${
              dashboardTab === 'macro'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Macro APIx Index & CPI</span>
          </button>

          <button
            onClick={() => setDashboardTab('airlines')}
            className={`pb-3 flex items-center space-x-2 transition-all border-b-2 ${
              dashboardTab === 'airlines'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Plane className="w-4 h-4" />
            <span>Airline Price Indices & Weights</span>
          </button>

          <button
            onClick={() => setDashboardTab('telemetry')}
            className={`pb-3 flex items-center space-x-2 transition-all border-b-2 ${
              dashboardTab === 'telemetry'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Corridor Telemetry & Governance</span>
          </button>

          <button
            onClick={() => setDashboardTab('live')}
            className={`pb-3 flex items-center space-x-2 transition-all border-b-2 ${
              dashboardTab === 'live'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Live Scraped Data ✦</span>
          </button>
        </div>

        {/* 4 Primary Top Metric KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Current APIx Composite</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-white font-mono">{chartData[chartData.length - 1]?.geksIndex || '168.45'}</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                <ArrowUpRight className="w-3 h-3 mr-0.5" /> +1.84% (DoD)
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block font-mono">Base Q1 2024 = 100 • 7D Low: 166.20</span>
          </div>

          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Weighted Median Fare (All In)</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-white font-mono">₹{chartData[chartData.length - 1]?.avgFare || '5,420'}</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                +₹210 (WoW)
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block font-mono">Yield: ₹4.82 / pax-km • Clean Base</span>
          </div>

          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">T+1 Urgent Surge Factor</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-amber-400 font-mono">1.44x</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
                High Pressure
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">vs 30-Day Benchmark • Spread: +₹2,430</span>
          </div>

          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Pipeline Ingestion Health</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-emerald-400 font-mono">99.82%</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                Purity
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">4.23M Quotes Cleaned • Latency: 38ms</span>
          </div>
        </div>

        {/* TAB 1: MACRO APIX INDEX & CPI */}
        {dashboardTab === 'macro' && (
          <div className="space-y-8">
            
            {/* Live Scenario Simulator Banner */}
            <div className="p-4 rounded-2xl bg-sky-950/40 border border-sky-500/30 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <span className="text-xs font-bold uppercase text-sky-300 tracking-wider flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-sky-400" />
                  Live Market Scenario Simulator (Stress-Test GEKS Index)
                </span>
                <span className="text-[11px] text-slate-400">
                  Active Scenario: <strong className="text-white font-mono">{SIMULATION_PRESETS.find(p=>p.id===activePreset)?.label}</strong>
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {SIMULATION_PRESETS.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => setActivePreset(preset.id)}
                    className={`p-2.5 rounded-xl border text-xs font-bold text-left transition-all ${
                      activePreset === preset.id
                        ? 'bg-sky-600 text-white border-sky-400 shadow-lg scale-[1.02]'
                        : 'bg-slate-900/90 text-slate-300 border-slate-800 hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span>{preset.label}</span>
                      {activePreset === preset.id && <Check className="w-3.5 h-3.5 text-white" />}
                    </div>
                    <span className={`text-[10px] block mt-1 font-normal ${activePreset === preset.id ? 'text-sky-100' : 'text-slate-500'}`}>
                      {preset.desc}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Main Multi-Series Line Chart */}
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-sky-400" />
                    APIx Index Trend vs MoSPI Air Transport CPI
                  </h3>
                  <p className="text-xs text-slate-400">
                    Continuous GEKS-Jevons multilateral airfare inflation tracking with 95% confidence intervals
                  </p>
                </div>

                {/* Series Toggles */}
                <div className="flex flex-wrap items-center gap-3 text-xs font-semibold">
                  <button 
                    onClick={() => setShowGEKS(!showGEKS)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                      showGEKS ? 'bg-sky-500/20 text-sky-300 border-sky-500/40' : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
                    }`}
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span>
                    <span>APEX-IND GEKS</span>
                  </button>

                  <button 
                    onClick={() => setShowLaspeyres(!showLaspeyres)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                      showLaspeyres ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
                    }`}
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                    <span>Chained Laspeyres</span>
                  </button>

                  <button 
                    onClick={() => setShowMoSPI(!showMoSPI)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                      showMoSPI ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
                    }`}
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                    <span>MoSPI Official</span>
                  </button>
                </div>
              </div>

              <div className="w-full h-80 sm:h-96 pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="geksGlow" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.35}/>
                        <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} domain={['dataMin - 5', 'dataMax + 5']} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#090d16', borderColor: '#38bdf833', borderRadius: '12px', color: '#fff', fontSize: '12px' }} 
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    
                    {showGEKS && (
                      <Area type="monotone" dataKey="geksIndex" name="APEX-IND GEKS (Drift-Free)" stroke="#38bdf8" strokeWidth={3} fillOpacity={1} fill="url(#geksGlow)" />
                    )}
                    {showLaspeyres && (
                      <Line type="monotone" dataKey="laspeyresIndex" name="Chained Laspeyres (Drifted)" stroke="#f43f5e" strokeWidth={2} strokeDasharray="4 4" dot={false} />
                    )}
                    {showMoSPI && (
                      <Line type="monotone" dataKey="mospiCPI" name="MoSPI CPI Official" stroke="#10b981" strokeWidth={2} dot={false} />
                    )}
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs font-semibold">
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                  <span className="text-slate-400 block text-[10px] uppercase">Festive Peak Surge</span>
                  <span className="text-rose-400 font-mono text-sm mt-0.5 block">Nov (Diwali): 178.8</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                  <span className="text-slate-400 block text-[10px] uppercase">Monsoon Trough</span>
                  <span className="text-sky-400 font-mono text-sm mt-0.5 block">Jul (Off-Peak): 148.4</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                  <span className="text-slate-400 block text-[10px] uppercase">Current Volatility Index</span>
                  <span className="text-emerald-400 font-mono text-sm mt-0.5 block">1.24σ (Normalized)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: AIRLINE PRICE INDICES & WEIGHTS */}
        {dashboardTab === 'airlines' && (
          <AirlineAnalytics />
        )}

        {/* TAB 4: LIVE SCRAPED DATA — real backend */}
        {dashboardTab === 'live' && (
          <LiveDataPanel />
        )}

        {/* TAB 3: CORRIDOR TELEMETRY & GOVERNANCE */}
        {dashboardTab === 'telemetry' && (
          <div className="space-y-8">
            
            {/* Data Quality & Governance Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <div className="glass-panel p-6 rounded-3xl space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Governance & Compliance
                </h4>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Axiomatic Transitivity Score:</span>
                    <span className="font-mono font-bold text-emerald-400">{GOVERNANCE_STATS.transitivityScore}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Missing Quote Imputation:</span>
                    <span className="font-mono font-bold text-slate-200">{GOVERNANCE_STATS.missingQuoteImputation}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Route Sample Breadth:</span>
                    <span className="font-mono font-bold text-sky-400">{GOVERNANCE_STATS.routeBreadth}</span>
                  </div>
                </div>
              </div>

              <div className="glass-panel p-6 rounded-3xl space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-sky-400" />
                  Booking Window Multipliers
                </h4>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  {BOOKING_WINDOWS.slice(0, 3).map((win) => (
                    <div key={win.bucket} className="p-2 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block">{win.bucket.split(' ')[0]}</span>
                      <span className="font-mono font-bold text-sky-400 text-sm">{win.multiplier}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-panel p-6 rounded-3xl space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Compass className="w-4 h-4 text-blue-400" />
                  India Airspace Telemetry
                </h4>
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-1">
                  <span className="font-mono font-bold text-sky-400 block">456 Active Route Pairs</span>
                  <p className="text-slate-400 text-[11px]">
                    Continuous tracking across Delhi (DEL), Mumbai (BOM), Bengaluru (BLR), and Kolkata (CCU) corridors.
                  </p>
                </div>
              </div>

            </div>

            {/* LIVE MONITORED DOMESTIC CORRIDORS TABLE (Matching Reference Image) */}
            <div className="glass-panel p-6 rounded-3xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="text-base font-bold text-white flex items-center gap-2">
                    <Activity className="w-4 h-4 text-sky-400" />
                    Live Monitored Domestic Corridors (456 Tracked)
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
                    className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-sky-500 w-52"
                  />
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px]">
                    <tr>
                      <th className="p-3.5 rounded-l-lg">Route</th>
                      <th className="p-3.5">Carrier & Flight</th>
                      <th className="p-3.5">Departure Horizon</th>
                      <th className="p-3.5">Clean Base Fare</th>
                      <th className="p-3.5">Taxes & UDF</th>
                      <th className="p-3.5">Total Realized</th>
                      <th className="p-3.5">vs 30D Index</th>
                      <th className="p-3.5 rounded-r-lg">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-medium">
                    {filteredCorridors.map((row) => (
                      <tr key={row.id} className="hover:bg-slate-900/60 transition-colors">
                        <td className="p-3.5 font-mono font-bold text-white">{row.route}</td>
                        <td className="p-3.5 font-mono text-slate-200">{row.carrier}</td>
                        <td className="p-3.5 text-slate-400">{row.horizon}</td>
                        <td className="p-3.5 font-mono text-slate-300">₹{row.baseFare}</td>
                        <td className="p-3.5 font-mono text-slate-400">₹{row.taxes}</td>
                        <td className="p-3.5 font-mono font-bold text-white text-sm">₹{row.totalFare}</td>
                        <td className={`p-3.5 font-mono font-bold ${row.vs30d.startsWith('+') ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {row.vs30d}
                        </td>
                        <td className="p-3.5">
                          <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold border ${row.statusStyle}`}>
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
