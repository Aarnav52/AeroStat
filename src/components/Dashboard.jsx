import React, { useState, useMemo } from 'react';
import { 
  ResponsiveContainer, LineChart as ReLineChart, Line, XAxis, YAxis, 
  Tooltip, CartesianGrid, Legend, AreaChart, Area 
} from 'recharts';
import { 
  BarChart3, Calendar, Download, Filter, RefreshCw, ArrowUpRight, 
  ArrowDownRight, Search, ShieldCheck, AlertTriangle, Layers, Info, Check, Sparkles, Zap, Activity
} from 'lucide-react';
import { 
  generateTimeSeriesData, TOP_ROUTES_DATA, 
  AIRLINE_BREAKDOWN, BOOKING_WINDOWS, LIVE_TICKER_FEED,
  SIMULATION_PRESETS, ANOMALY_LOGS
} from '../data/mockData';

export default function Dashboard() {
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

  // Find active preset shock factor
  const activeShockFactor = useMemo(() => {
    const p = SIMULATION_PRESETS.find(x => x.id === activePreset);
    return p ? p.shockFactor : 1.0;
  }, [activePreset]);

  // Dynamic time series dataset based on range filter and simulation preset
  const chartData = useMemo(() => {
    return generateTimeSeriesData(timeRange, activeShockFactor);
  }, [timeRange, activeShockFactor]);

  // Filtered live routes for data table
  const filteredRoutes = useMemo(() => {
    return TOP_ROUTES_DATA.filter(r => {
      const matchRoute = selectedRoute === 'ALL' || r.route.includes(selectedRoute);
      const matchSearch = r.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          r.route.toLowerCase().includes(searchTerm.toLowerCase());
      return matchRoute && matchSearch;
    });
  }, [selectedRoute, searchTerm]);

  // CSV Export feature
  const handleExportCSV = () => {
    const headers = ["Date", "GEKS_Index", "Laspeyres_Index", "MoSPI_CPI_Transport", "Avg_Domestic_Fare_INR", "Volatility"];
    const rows = chartData.map(row => [
      row.fullDate,
      row.geksIndex,
      row.laspeyresIndex,
      row.mospiCPI,
      row.avgFare,
      row.volatility
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `APEX_IND_Airfare_Index_${timeRange}_${activePreset}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setExportMessage('CSV Download Started!');
    setTimeout(() => setExportMessage(''), 3000);
  };

  // JSON Export feature
  const handleExportJSON = () => {
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(chartData, null, 2))}`;
    const link = document.createElement("a");
    link.setAttribute("href", jsonString);
    link.setAttribute("download", `APEX_IND_Airfare_Index_${timeRange}_${activePreset}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setExportMessage('JSON Download Started!');
    setTimeout(() => setExportMessage(''), 3000);
  };

  return (
    <section id="dashboard" className="py-16 bg-slate-950 text-slate-100 border-t border-slate-800 relative">
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Dashboard Header Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-sans tracking-tight">
                APEX-IND Real-Time Airfare Intelligence Dashboard
              </h2>
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
                LIVE UPDATES
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Multilateral GEKS daily benchmark calibrated against MoSPI CPI Transport weightings.
            </p>
          </div>

          {/* Time Range Selector & Export Controls */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
              {['7D', '30D', '90D', '1Y', 'ALL'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1.5 rounded-lg transition-all ${
                    timeRange === range 
                      ? 'bg-sky-500 text-white shadow-md shadow-sky-500/30' 
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleExportCSV}
                className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold rounded-xl text-slate-200 bg-slate-900 border border-slate-700 hover:bg-slate-800 transition-all shadow-sm"
              >
                <Download className="w-3.5 h-3.5 text-sky-400" />
                <span>CSV</span>
              </button>

              <button
                onClick={handleExportJSON}
                className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold rounded-xl text-slate-200 bg-slate-900 border border-slate-700 hover:bg-slate-800 transition-all shadow-sm"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span>JSON</span>
              </button>
            </div>

            {exportMessage && (
              <span className="text-xs font-semibold text-emerald-400 animate-pulse">
                {exportMessage}
              </span>
            )}
          </div>
        </div>

        {/* Live Market Simulation Controls Banner */}
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
                    ? 'bg-sky-600 text-white border-sky-400 shadow-lg shadow-sky-500/25 scale-[1.02]'
                    : 'bg-slate-900/90 text-slate-300 border-slate-800 hover:bg-slate-800 hover:border-slate-700'
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

        {/* Filter Controls Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800/80 backdrop-blur-md">
          
          <div>
            <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1.5">Corridor Route</label>
            <select
              value={selectedRoute}
              onChange={(e) => setSelectedRoute(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All 120 Domestic Routes</option>
              <option value="DEL">Delhi Corridors (DEL)</option>
              <option value="BOM">Mumbai Corridors (BOM)</option>
              <option value="BLR">Bengaluru Corridors (BLR)</option>
              <option value="CCU">Kolkata Corridors (CCU)</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1.5">Booking Lead Window</label>
            <select
              value={selectedWindow}
              onChange={(e) => setSelectedWindow(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Windows (T-0 to T-45)</option>
              <option value="T-0">T-0 (Same Day)</option>
              <option value="T-7">T-7 (1 Week Lead)</option>
              <option value="T-14">T-14 (2 Weeks Lead)</option>
              <option value="T-30">T-30 (1 Month Lead)</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1.5">Airline Filter</label>
            <select
              value={selectedAirline}
              onChange={(e) => setSelectedAirline(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Airlines (IndiGo, AI, Vistara, Akasa)</option>
              <option value="IndiGo">IndiGo (6E)</option>
              <option value="Air India">Air India Group (AI/UK)</option>
              <option value="Akasa Air">Akasa Air (QP)</option>
              <option value="SpiceJet">SpiceJet (SG)</option>
            </select>
          </div>

          <div className="flex items-end space-x-2">
            <button
              onClick={() => { setSelectedRoute('ALL'); setSelectedWindow('ALL'); setSelectedAirline('ALL'); setSearchTerm(''); setActivePreset('normal'); }}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl px-3 py-2 transition-all flex items-center justify-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset Filters</span>
            </button>
          </div>

        </div>

        {/* 4 Primary KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Airfare Index Value</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-white font-mono">{chartData[chartData.length - 1]?.geksIndex || '168.45'}</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                <ArrowUpRight className="w-3 h-3 mr-0.5" /> +1.42%
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">Multilateral GEKS Transitive Index</span>
          </div>

          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Avg 1-Way Fare</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-white font-mono">₹{chartData[chartData.length - 1]?.avgFare || '5,420'}</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                +₹140 7d
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">Weighted across 120 route corridors</span>
          </div>

          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">30-Day Volatility</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-white font-mono">0.0394</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
                -0.0008
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">Price dispersion standard deviation</span>
          </div>

          <div className="glass-panel p-5 rounded-2xl glass-card-glow">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Direct Route Ratio</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-extrabold text-sky-400 font-mono">98.82%</span>
              <span className="inline-flex items-center text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                +0.05%
              </span>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">Live fare availability coverage</span>
          </div>
        </div>

        {/* MAIN CHART PANEL */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-6">
          
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-sky-400" />
                Airfare Price Index Trends ({timeRange})
              </h3>
              <p className="text-xs text-slate-400">
                Comparing Multilateral GEKS (Drift-Free) against Chained Laspeyres and MoSPI CPI Transport Benchmark
              </p>
            </div>

            {/* Series Toggles */}
            <div className="flex flex-wrap items-center gap-3 text-xs font-semibold">
              <button 
                onClick={() => setShowGEKS(!showGEKS)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                  showGEKS 
                    ? 'bg-sky-500/20 text-sky-300 border-sky-500/40' 
                    : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
                }`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span>
                <span>APEX-IND GEKS</span>
              </button>

              <button 
                onClick={() => setShowLaspeyres(!showLaspeyres)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                  showLaspeyres 
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' 
                    : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
                }`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                <span>Chained Laspeyres</span>
              </button>

              <button 
                onClick={() => setShowMoSPI(!showMoSPI)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                  showMoSPI 
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
                    : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
                }`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                <span>MoSPI CPI Benchmark</span>
              </button>
            </div>
          </div>

          {/* Recharts Component */}
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
                  contentStyle={{ 
                    backgroundColor: '#090d16', 
                    borderColor: '#38bdf833', 
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.8)',
                    color: '#fff',
                    fontSize: '12px'
                  }} 
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                
                {showGEKS && (
                  <Area 
                    type="monotone" 
                    dataKey="geksIndex" 
                    name="APEX-IND GEKS (Drift-Free)" 
                    stroke="#38bdf8" 
                    strokeWidth={3}
                    fillOpacity={1} 
                    fill="url(#geksGlow)" 
                  />
                )}

                {showLaspeyres && (
                  <Line 
                    type="monotone" 
                    dataKey="laspeyresIndex" 
                    name="Chained Laspeyres (Drifted)" 
                    stroke="#f43f5e" 
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                )}

                {showMoSPI && (
                  <Line 
                    type="monotone" 
                    dataKey="mospiCPI" 
                    name="MoSPI CPI Transport" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    dot={false}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-400 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <span className="flex items-center gap-1.5 text-slate-300">
              <Info className="w-4 h-4 text-sky-400 shrink-0" />
              <span>Chain Drift Gap: Laspeyres overestimates inflation by <strong>+4.18 index points</strong> due to price bouncing. GEKS eliminates this variance.</span>
            </span>
            <span className="font-mono text-sky-400 font-bold">MoSPI Base: 2024=100</span>
          </div>

        </div>

        {/* SECONDARY ANALYTICS GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Top Corridor Heatmap & Table */}
          <div className="lg:col-span-7 glass-panel p-6 rounded-3xl space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-sky-400" />
                Domestic Corridor Fare Analysis
              </h4>
              
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
                <input 
                  type="text" 
                  placeholder="Search route (e.g. DEL, BOM)..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-sky-500 w-44"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px]">
                  <tr>
                    <th className="p-3 rounded-l-lg">Corridor</th>
                    <th className="p-3">Volume Share</th>
                    <th className="p-3">Avg Fare</th>
                    <th className="p-3">7D Change</th>
                    <th className="p-3 rounded-r-lg">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {filteredRoutes.map((route) => (
                    <tr key={route.rank} className="hover:bg-slate-900/50 transition-colors">
                      <td className="p-3 font-mono font-bold text-white">{route.name} ({route.route})</td>
                      <td className="p-3 font-mono text-slate-300">{route.volume}</td>
                      <td className="p-3 font-mono text-white font-bold">₹{Math.round(route.avgFare * activeShockFactor)}</td>
                      <td className={`p-3 font-mono font-bold ${route.change7d.startsWith('+') ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {route.change7d}
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          route.status === 'High Demand' 
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' 
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {route.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Anomaly & De-Noising Live Logs Panel */}
          <div className="lg:col-span-5 glass-panel p-6 rounded-3xl space-y-4">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Live De-Noising Anomaly Stream
            </h4>

            <div className="space-y-2.5">
              {ANOMALY_LOGS.map((log) => (
                <div key={log.id} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-white">{log.route}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">{log.type}</span>
                    </div>
                    <span className="text-[11px] text-slate-400 mt-1 block">Scraped: <strong className="text-slate-300">{log.rawFare}</strong> • {log.time}</span>
                  </div>

                  <span className="font-mono font-bold text-emerald-400 text-xs px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20">
                    {log.action}
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-2">
              <div className="p-3 rounded-xl bg-sky-950/40 border border-sky-500/30 text-[11px] text-sky-200">
                ⚡ <strong>99.8% Anomaly Prevention</strong>: Prevents price manipulation by web scraping bots and promo code glitches.
              </div>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
}
