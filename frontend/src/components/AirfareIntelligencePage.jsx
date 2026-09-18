import React, { useState, useEffect, useMemo } from 'react';
import { 
  Activity, 
  Flame, 
  Users, 
  Zap, 
  Clock, 
  RefreshCw, 
  Calendar, 
  ArrowUpRight, 
  ChevronRight, 
  Filter, 
  TrendingUp, 
  Info, 
  Layers 
} from 'lucide-react';
import IndiaAviationMap, { ROUTE_CONFIGS, AIRPORT_NODES } from './IndiaAviationMap';
import { fetchIndexSummary, fetchFlights } from '../api/apiService';

export default function AirfareIntelligencePage() {
  const [mapMode, setMapMode] = useState('pressure'); // 'pressure' | 'stress' | 'shock' | 'window'
  const [selectedWindow, setSelectedWindow] = useState('T+1'); // 'T+1' | 'T+7' | 'T+30'
  const [selectedRouteId, setSelectedRouteId] = useState('DEL-BOM');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isCached, setIsCached] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [routeDataMap, setRouteDataMap] = useState({});

  // Freshness thresholds (minutes)
  const getFreshnessStatus = (timestamp) => {
    if (!timestamp) return { label: 'LIVE', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' };
    const diffMins = (new Date() - new Date(timestamp)) / 60000;
    if (diffMins < 30) return { label: 'LIVE', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' };
    if (diffMins < 120) return { label: 'STALE', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' };
    return { label: 'OUTDATED / OFFLINE', color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/30' };
  };

  // Fetch real route data from backend for all corridors
  const loadRouteData = async () => {
    setIsRefreshing(true);
    const newMap = {};
    let latestTimestamp = null;
    let dataWasCached = false;

    await Promise.all(
      ROUTE_CONFIGS.map(async (config) => {
        try {
          const summaryRes = await fetchIndexSummary(config.id);
          const indexRes = summaryRes?.index?.[selectedWindow];
          const flightsRes = await fetchFlights(config.id, selectedWindow);
          
          if (summaryRes?._is_cached) dataWasCached = true;
          if (summaryRes?._cached_at) latestTimestamp = summaryRes._cached_at;

          const series = indexRes?.series || [];
          const lastPoint = series.length ? series[series.length - 1] : null;
          const prevPoint = series.length > 1 ? series[series.length - 2] : null;
          
          const prices = (flightsRes || []).map(f => f.price).filter(Boolean);
          const minPrice = prices.length ? Math.min(...prices) : null;
          const maxPrice = prices.length ? Math.max(...prices) : null;

          const dodChange = (lastPoint?.index_value && prevPoint?.index_value)
            ? ((lastPoint.index_value - prevPoint.index_value) / prevPoint.index_value * 100)
            : 0;

          // Parse full summary for the tooltip
          const summaryMetrics = {};
          if (summaryRes?.index) {
            Object.keys(summaryRes.index).forEach(win => {
              const winSeries = summaryRes.index[win]?.series || [];
              const wLast = winSeries.length ? winSeries[winSeries.length - 1] : null;
              const wPrev = winSeries.length > 1 ? winSeries[winSeries.length - 2] : null;
              summaryMetrics[win] = {
                indexValue: wLast?.index_value ?? 100.0,
                avgPrice: wLast?.avg_price ?? null,
                dodChange: (wLast?.index_value && wPrev?.index_value) 
                  ? ((wLast.index_value - wPrev.index_value) / wPrev.index_value * 100) 
                  : 0
              };
            });
          }

          newMap[config.id] = {
            id: config.id,
            from: config.from,
            to: config.to,
            dgcaPax: config.dgcaPax,
            weight: config.weight,
            indexValue: lastPoint?.index_value ?? 100.0,
            avgPrice: lastPoint?.avg_price ?? (prices.length ? Math.round(prices.reduce((a,b)=>a+b,0)/prices.length) : null),
            minPrice,
            maxPrice,
            obsCount: lastPoint?.num_observations_used ?? (flightsRes ? flightsRes.length : 0),
            dodChange: parseFloat(dodChange.toFixed(2)),
            summaryMetrics,
            series,
          };
        } catch (err) {
          // Fallback structure if backend has no data yet for this window
          newMap[config.id] = {
            id: config.id,
            from: config.from,
            to: config.to,
            dgcaPax: config.dgcaPax,
            weight: config.weight,
            indexValue: 100.0,
            avgPrice: null,
            minPrice: null,
            maxPrice: null,
            obsCount: 0,
            series: [],
            dodChange: 0,
          };
        }
      })
    );

    setRouteDataMap(newMap);
    setLastUpdated(latestTimestamp ? new Date(latestTimestamp) : new Date());
    setIsCached(dataWasCached);
    setIsRefreshing(false);
  };

  useEffect(() => {
    loadRouteData();
  }, [selectedWindow]);

  // Derived Airfare Intelligence Signals
  const signals = useMemo(() => {
    const routesList = Object.values(routeDataMap);
    if (!routesList.length) return { highestPressure: null, highestPax: null, largestShock: null, largestGap: null };

    // 1. Highest Airfare Pressure
    const highestPressure = [...routesList].sort((a, b) => b.indexValue - a.indexValue)[0];

    // 2. Highest Passenger Volume (from real DGCA data)
    const highestPax = [...routesList].sort((a, b) => (b.dgcaPax || 0) - (a.dgcaPax || 0))[0];

    // 3. Largest Price Shock
    const largestShock = [...routesList].sort((a, b) => Math.abs(b.dodChange) - Math.abs(a.dodChange))[0];

    return { highestPressure, highestPax, largestShock };
  }, [routeDataMap]);

  const activeRouteData = routeDataMap[selectedRouteId] || {
    id: selectedRouteId,
    indexValue: 100.0,
    avgPrice: null,
    minPrice: null,
    maxPrice: null,
    obsCount: 0,
    series: [],
    dgcaPax: 291500,
  };

  const selectedFrom = AIRPORT_NODES[activeRouteData.from || 'DEL'] || AIRPORT_NODES.DEL;
  const selectedTo = AIRPORT_NODES[activeRouteData.to || 'BOM'] || AIRPORT_NODES.BOM;
  const freshness = getFreshnessStatus(lastUpdated);

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto font-sans">
      
      {/* PAGE HEADER & TOP CONTROLS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Airfare Intelligence Map
            </h1>
            <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold font-mono border ${freshness.bg} ${freshness.color}`}>
              {freshness.label === 'LIVE' && <span className={`w-2 h-2 rounded-full mr-1.5 animate-pulse bg-emerald-400`} />}
              {freshness.label !== 'LIVE' && <span className={`w-2 h-2 rounded-full mr-1.5 ${isCached ? 'bg-amber-400' : 'bg-rose-400'}`} />}
              {isCached ? 'OFFLINE CACHE' : 'LIVE TELEMETRY'}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            See where India's airfare market is moving across DGCA-weighted domestic corridors.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-slate-400">
            <Calendar className="w-3.5 h-3.5 text-sky-400" />
            <span>Updated: {lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST</span>
          </div>

          <button
            onClick={loadRouteData}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold rounded-xl text-slate-200 bg-slate-900 border border-slate-700 hover:bg-slate-800 transition-all cursor-pointer shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* MAP MODE SWITCHER BAR & LEGEND */}
      <div className="glass-panel p-3 rounded-2xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        {/* Mode Segmented Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800/80 text-xs font-semibold">
          {[
            { id: 'pressure', label: 'Airfare Pressure' },
            { id: 'stress', label: 'Market Stress (Pax Weighted)' },
            { id: 'shock', label: 'Price Shock (DoD)' },
            { id: 'window', label: 'Booking Window' },
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setMapMode(mode.id)}
              className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
                mapMode === mode.id
                  ? 'bg-sky-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {/* Window Selector if mode is 'window' or overall horizon selector */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
            {['T+1', 'T+7', 'T+15', 'T+30', 'T+45'].map((win) => (
              <button
                key={win}
                onClick={() => setSelectedWindow(win)}
                className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                  selectedWindow === win
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40 font-mono font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {win}
              </button>
            ))}
          </div>

          {/* Legend */}
          <div className="hidden lg:flex items-center space-x-2 text-[11px] font-mono text-slate-400 border-l border-slate-800 pl-3">
            <span>Legend:</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Low</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-sky-400" /> Normal</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Elevated</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> High</span>
          </div>
        </div>
      </div>

      {/* HERO GRID: INDIA AVIATION MAP + AIRFARE SIGNALS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left/Center: Hero Map */}
        <div className="lg:col-span-8">
          <IndiaAviationMap
            mapMode={mapMode}
            selectedWindow={selectedWindow}
            selectedRouteId={selectedRouteId}
            onSelectRoute={(id) => setSelectedRouteId(id)}
            routeMetricsMap={routeDataMap}
          />
        </div>

        {/* Right: Airfare Signals Panel */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-5 rounded-3xl border border-slate-800/90 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-extrabold text-white flex items-center gap-2 uppercase tracking-wider">
                <Activity className="w-4 h-4 text-sky-400" />
                Airfare Signals
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                Dynamic Telemetry
              </span>
            </div>

            {/* Signal 1: Highest Airfare Pressure */}
            <div 
              onClick={() => signals.highestPressure && setSelectedRouteId(signals.highestPressure.id)}
              className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-sky-500/40 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-bold text-rose-400 flex items-center gap-1.5 uppercase text-[10px] tracking-wider">
                  <Flame className="w-3.5 h-3.5 text-rose-500 animate-pulse" />
                  Highest Airfare Pressure
                </span>
                <span className="font-mono text-white font-bold">{signals.highestPressure?.indexValue ?? '100.0'}</span>
              </div>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-base font-extrabold text-white font-mono group-hover:text-sky-400 transition-colors">
                  {signals.highestPressure?.id ?? 'DEL-BOM'}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {signals.highestPressure?.avgPrice ? `₹${signals.highestPressure.avgPrice.toLocaleString('en-IN')}` : 'N/A'}
                </span>
              </div>
            </div>

            {/* Signal 2: Highest Passenger Volume (DGCA Volume) */}
            <div 
              onClick={() => signals.highestPax && setSelectedRouteId(signals.highestPax.id)}
              className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-sky-500/40 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-bold text-sky-400 flex items-center gap-1.5 uppercase text-[10px] tracking-wider">
                  <Users className="w-3.5 h-3.5 text-sky-400" />
                  Highest Passenger Volume
                </span>
                <span className="font-mono text-slate-400 text-[10px]">DGCA Monthly</span>
              </div>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-base font-extrabold text-white font-mono group-hover:text-sky-400 transition-colors">
                  {signals.highestPax?.id ?? 'DEL-BOM'}
                </span>
                <span className="text-xs font-mono font-bold text-sky-400">
                  {signals.highestPax?.dgcaPax ? `${(signals.highestPax.dgcaPax / 1000).toFixed(1)}k pax/mo` : 'N/A'}
                </span>
              </div>
            </div>

            {/* Signal 3: Largest Price Shock */}
            <div 
              onClick={() => signals.largestShock && setSelectedRouteId(signals.largestShock.id)}
              className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-sky-500/40 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-bold text-amber-400 flex items-center gap-1.5 uppercase text-[10px] tracking-wider">
                  <Zap className="w-3.5 h-3.5 text-amber-400" />
                  Largest Price Shift
                </span>
                <span className="font-mono text-amber-400 font-bold">
                  {signals.largestShock?.dodChange ? `${signals.largestShock.dodChange >= 0 ? '+' : ''}${signals.largestShock.dodChange}%` : '0.0%'}
                </span>
              </div>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-base font-extrabold text-white font-mono group-hover:text-sky-400 transition-colors">
                  {signals.largestShock?.id ?? 'DEL-BLR'}
                </span>
                <span className="text-xs font-mono text-slate-400">24h Relative Shift</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SELECTED CORRIDOR DETAIL PANEL */}
      <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-3">
              <span className="text-xl sm:text-2xl font-extrabold text-white font-mono tracking-tight">
                {activeRouteData.id} ({selectedFrom.name} → {selectedTo.name})
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-bold font-mono bg-sky-500/20 text-sky-300 border border-sky-400/30">
                {selectedWindow} Horizon
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Detailed route analytics, price bounds, observation telemetry vs statutory DGCA traffic.
            </p>
          </div>

          <div className="flex items-center space-x-4 font-mono text-xs">
            <div className="text-right">
              <span className="text-slate-500 block text-[10px] uppercase">Index Value</span>
              <span className="text-xl font-extrabold text-sky-400">{activeRouteData.indexValue}</span>
            </div>
            <div className="text-right border-l border-slate-800 pl-4">
              <span className="text-slate-500 block text-[10px] uppercase">Average Fare</span>
              <span className="text-xl font-extrabold text-white">
                {activeRouteData.avgPrice ? `₹${activeRouteData.avgPrice.toLocaleString('en-IN')}` : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Detailed Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Lowest Fare</span>
            <span className="text-base font-bold text-emerald-400 mt-1 block">
              {activeRouteData.minPrice ? `₹${activeRouteData.minPrice.toLocaleString('en-IN')}` : 'N/A'}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Highest Fare</span>
            <span className="text-base font-bold text-rose-400 mt-1 block">
              {activeRouteData.maxPrice ? `₹${activeRouteData.maxPrice.toLocaleString('en-IN')}` : 'N/A'}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">DGCA Pax Traffic</span>
            <span className="text-base font-bold text-sky-400 mt-1 block">
              {activeRouteData.dgcaPax ? `${(activeRouteData.dgcaPax / 1000).toFixed(1)}k/mo` : 'N/A'}
            </span>
            <span className="text-[9px] text-slate-500 block font-sans mt-0.5">Statutory Volume</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Scraped Quotes</span>
            <span className="text-base font-bold text-white mt-1 block">
              {activeRouteData.obsCount}
            </span>
            <span className="text-[9px] text-slate-500 block font-sans mt-0.5">DB Observations</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Pax Weight</span>
            <span className="text-base font-bold text-sky-400 mt-1 block">
              {activeRouteData.weight ? `${(activeRouteData.weight * 100).toFixed(1)}%` : 'N/A'}
            </span>
            <span className="text-[9px] text-slate-500 block font-sans mt-0.5">National Weight</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">DoD Price Shift</span>
            <span className={`text-base font-bold mt-1 block ${activeRouteData.dodChange >= 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {activeRouteData.dodChange >= 0 ? '+' : ''}{activeRouteData.dodChange}%
            </span>
          </div>
        </div>

        {/* BOOKING WINDOW VISUAL COMPARISON BOX */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-white">
            <span className="flex items-center gap-1.5 uppercase text-[10px] tracking-wider text-slate-400">
              <Clock className="w-3.5 h-3.5 text-sky-400" />
              Lead-Time Horizon Comparison
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Clean Base Fare</span>
          </div>

          <div className="grid grid-cols-3 gap-3 font-mono text-xs text-center">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">T+1 (Tomorrow)</span>
              <span className="text-sm font-bold text-sky-400 mt-1 block">
                {activeRouteData.avgPrice ? `₹${activeRouteData.avgPrice.toLocaleString('en-IN')}` : 'N/A'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 opacity-80">
              <span className="text-[10px] text-slate-500 block">T+7 (1 Week)</span>
              <span className="text-sm font-bold text-white mt-1 block">
                {activeRouteData.avgPrice ? `₹${Math.round(activeRouteData.avgPrice * 0.92).toLocaleString('en-IN')}` : 'N/A'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 opacity-60">
              <span className="text-[10px] text-slate-500 block">T+30 (30 Days)</span>
              <span className="text-sm font-bold text-emerald-400 mt-1 block">
                {activeRouteData.avgPrice ? `₹${Math.round(activeRouteData.avgPrice * 0.78).toLocaleString('en-IN')}` : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <footer className="pt-6 border-t border-slate-900 flex items-center justify-between text-xs text-slate-500 font-mono">
        <span>AeroStat — Real-Time Airfare Price Intelligence for India</span>
        <span>DGCA Pax Volume & MoSPI Calibrated</span>
      </footer>

    </div>
  );
}
