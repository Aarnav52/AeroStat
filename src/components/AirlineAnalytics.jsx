import React, { useState, useMemo } from 'react';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend 
} from 'recharts';
import { Plane, BarChart2, Layers, Info, Filter, Sparkles, ShieldCheck } from 'lucide-react';
import { generateAirlineTimeSeriesData, AIRLINE_WEIGHTED_TABLE } from '../data/mockData';

export default function AirlineAnalytics() {
  const [timeRange, setTimeRange] = useState('90D');
  
  // Carrier toggles
  const [showIndigo, setShowIndigo] = useState(true);
  const [showAirIndia, setShowAirIndia] = useState(true);
  const [showAkasa, setShowAkasa] = useState(true);
  const [showSpicejet, setShowSpicejet] = useState(true);

  // Generate dynamic time series dataset
  const airlineData = useMemo(() => {
    return generateAirlineTimeSeriesData(timeRange);
  }, [timeRange]);

  // Calculate composite weighted index sum
  const compositeWeightedIndex = useMemo(() => {
    return AIRLINE_WEIGHTED_TABLE.reduce((sum, item) => sum + parseFloat(item.weightedPoints), 0).toFixed(2);
  }, []);

  return (
    <div className="space-y-8">
      
      {/* Top Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/30">
              <Plane className="w-4 h-4" />
            </span>
            <h3 className="text-xl font-extrabold text-white font-sans">
              Airline-Wise Airfare Index & Capacity Telemetry
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Independent carrier price yield surveillance tracking IndiGo, Air India Group, Akasa Air, and SpiceJet.
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-semibold self-start sm:self-auto">
          {['7D', '30D', '90D', '1Y'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                timeRange === range 
                  ? 'bg-sky-500 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* CHART MODULE: Airline-Wise Index Graph */}
      <div className="glass-panel p-6 rounded-3xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-sky-400" />
              Carrier Price Indices Trajectory ({timeRange})
            </h4>
            <p className="text-xs text-slate-400">
              Base Q1 2024 = 100 • Weighted against DGCA monthly passenger volume
            </p>
          </div>

          {/* Carrier Visibility Toggles */}
          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
            <button 
              onClick={() => setShowIndigo(!showIndigo)}
              className={`px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 ${
                showIndigo ? 'bg-blue-500/20 text-blue-300 border-blue-500/40' : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-blue-400"></span>
              <span>IndiGo (6E)</span>
            </button>

            <button 
              onClick={() => setShowAirIndia(!showAirIndia)}
              className={`px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 ${
                showAirIndia ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
              <span>Air India (AI+UK)</span>
            </button>

            <button 
              onClick={() => setShowAkasa(!showAkasa)}
              className={`px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 ${
                showAkasa ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
              <span>Akasa Air (QP)</span>
            </button>

            <button 
              onClick={() => setShowSpicejet(!showSpicejet)}
              className={`px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 ${
                showSpicejet ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40' : 'bg-slate-900 text-slate-500 border-slate-800 line-through'
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-400"></span>
              <span>SpiceJet (SG)</span>
            </button>
          </div>
        </div>

        {/* Multi-Line Recharts Component */}
        <div className="w-full h-80 sm:h-96 pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={airlineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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

              {showIndigo && (
                <Line type="monotone" dataKey="Indigo" name="IndiGo (6E - 61.4% Share)" stroke="#38bdf8" strokeWidth={2.5} dot={false} />
              )}
              {showAirIndia && (
                <Line type="monotone" dataKey="AirIndia" name="Air India Group (AI/UK - 28.2% Share)" stroke="#f43f5e" strokeWidth={2.5} dot={false} />
              )}
              {showAkasa && (
                <Line type="monotone" dataKey="AkasaAir" name="Akasa Air (QP - 4.8% Share)" stroke="#f59e0b" strokeWidth={2.5} dot={false} />
              )}
              {showSpicejet && (
                <Line type="monotone" dataKey="SpiceJet" name="SpiceJet (SG - 4.1% Share)" stroke="#eab308" strokeWidth={2} strokeDasharray="4 4" dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* TABLE MODULE: Airline-Weighted Index Table */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              Airline Weighting & Index Contribution Matrix
            </h4>
            <p className="text-xs text-slate-400">
              DGCA passenger traffic volume weighting applied to carrier base fare indices
            </p>
          </div>

          <span className="text-xs font-mono font-bold px-3 py-1 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/30">
            Composite Weighted Sum: {compositeWeightedIndex}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px]">
              <tr>
                <th className="p-3.5 rounded-l-lg">Airline Carrier</th>
                <th className="p-3.5">DGCA Share Weight</th>
                <th className="p-3.5">Base Price Index</th>
                <th className="p-3.5">Weighted Contribution</th>
                <th className="p-3.5">7D Shift</th>
                <th className="p-3.5">30D Shift</th>
                <th className="p-3.5">Active Fleet</th>
                <th className="p-3.5 rounded-r-lg">Carrier Model</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {AIRLINE_WEIGHTED_TABLE.map((item) => (
                <tr key={item.id} className="hover:bg-slate-900/60 transition-colors">
                  <td className="p-3.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white">{item.name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{item.code}</span>
                    </div>
                  </td>
                  <td className="p-3.5 font-mono text-sky-400 font-bold">{item.weightPercent}</td>
                  <td className="p-3.5 font-mono text-white font-bold">{item.baseIndex}</td>
                  <td className="p-3.5 font-mono text-emerald-400 font-extrabold">{item.weightedPoints} pts</td>
                  <td className={`p-3.5 font-mono font-bold ${item.shift7d.startsWith('+') ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {item.shift7d}
                  </td>
                  <td className={`p-3.5 font-mono font-bold ${item.shift30d.startsWith('+') ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {item.shift30d}
                  </td>
                  <td className="p-3.5 font-mono text-slate-300">{item.activeFleet} Aircraft</td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                      {item.category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>FSC vs LCC Premium Spread: Full Service Carriers (Air India) carry a <strong>+16.4% fare yield premium</strong> over LCC carriers.</span>
          </span>
          <span className="font-mono text-sky-400 font-bold">Base Q1 2024 = 100</span>
        </div>
      </div>

    </div>
  );
}
