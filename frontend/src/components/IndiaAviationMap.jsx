import React, { useState } from 'react';
import { Plane, Eye, Activity, ShieldAlert, ArrowUpRight } from 'lucide-react';

// Accurate SVG coordinate mappings for Indian Aviation Nodes (800x850 viewport)
export const AIRPORT_NODES = {
  DEL: { code: 'DEL', name: 'Delhi', full: 'Indira Gandhi Intl', x: 380, y: 220 },
  BOM: { code: 'BOM', name: 'Mumbai', full: 'Chhatrapati Shivaji Maharaj', x: 260, y: 500 },
  BLR: { code: 'BLR', name: 'Bengaluru', full: 'Kempegowda Intl', x: 360, y: 690 },
  HYD: { code: 'HYD', name: 'Hyderabad', full: 'Rajiv Gandhi Intl', x: 420, y: 540 },
  CCU: { code: 'CCU', name: 'Kolkata', full: 'Netaji Subhash Chandra Bose', x: 700, y: 390 },
  MAA: { code: 'MAA', name: 'Chennai', full: 'Chennai Intl', x: 460, y: 710 },
  AMD: { code: 'AMD', name: 'Ahmedabad', full: 'Sardar Vallabhbhai Patel', x: 240, y: 390 },
};

// Real DGCA Monthly Passenger Volumes (Statutory Data)
export const ROUTE_CONFIGS = [
  { id: 'DEL-BOM', from: 'DEL', to: 'BOM', dgcaPax: 291500, weight: 0.3013, curveOffset: -40 },
  { id: 'DEL-BLR', from: 'DEL', to: 'BLR', dgcaPax: 210000, weight: 0.2171, curveOffset: 30 },
  { id: 'BOM-BLR', from: 'BOM', to: 'BLR', dgcaPax: 164000, weight: 0.1695, curveOffset: -25 },
  { id: 'DEL-CCU', from: 'DEL', to: 'CCU', dgcaPax: 124000, weight: 0.1282, curveOffset: -35 },
  { id: 'MAA-DEL', from: 'MAA', to: 'DEL', dgcaPax: 89500, weight: 0.0925, curveOffset: 45 },
  { id: 'BLR-HYD', from: 'BLR', to: 'HYD', dgcaPax: 88500, weight: 0.0915, curveOffset: -20 },
  { id: 'DEL-HYD', from: 'DEL', to: 'HYD', dgcaPax: null, weight: 0.05, curveOffset: 15 },
  { id: 'AMD-DEL', from: 'AMD', to: 'DEL', dgcaPax: null, weight: 0.04, curveOffset: -25 },
];

export default function IndiaAviationMap({
  mapMode,
  selectedWindow,
  selectedRouteId,
  onSelectRoute,
  routeMetricsMap,
}) {
  const [hoveredRoute, setHoveredRoute] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Calculate SVG stroke-width based on DGCA Passenger Weight
  const getStrokeWidth = (weight) => {
    if (!weight) return 2.5;
    return Math.max(2.5, Math.min(8.5, weight * 22));
  };

  // Determine line color based on selected map mode and real route metrics
  const getCorridorColor = (routeId, metrics) => {
    const idxVal = metrics?.indexValue ?? 100.0;
    const shock = metrics?.dodChange ?? 0;

    if (mapMode === 'pressure' || mapMode === 'window') {
      if (idxVal > 110) return '#f43f5e'; // High (Rose)
      if (idxVal > 105) return '#f59e0b'; // Elevated (Amber)
      if (idxVal >= 100) return '#38bdf8'; // Normal (Sky Blue)
      return '#10b981'; // Discount (Emerald)
    }

    if (mapMode === 'stress') {
      const paxVol = metrics?.dgcaPax || 0;
      if (paxVol > 200000 && idxVal > 105) return '#f43f5e';
      if (idxVal > 105) return '#f59e0b';
      return '#38bdf8';
    }

    if (mapMode === 'shock') {
      if (Math.abs(shock) > 8) return '#f43f5e';
      if (Math.abs(shock) > 3) return '#f59e0b';
      return '#38bdf8';
    }

    return '#38bdf8';
  };

  // Generate curved SVG quadratic Bezier path
  const createCurvedPath = (fromNode, toNode, offset = 0) => {
    const mx = (fromNode.x + toNode.x) / 2;
    const my = (fromNode.y + toNode.y) / 2;
    const dx = toNode.x - fromNode.x;
    const dy = toNode.y - fromNode.y;
    const len = Math.sqrt(dx * dx + dy * dy);
    
    // Normal vector for curve arc
    const nx = -dy / len;
    const ny = dx / len;
    
    const cx = mx + nx * offset;
    const cy = my + ny * offset;

    return {
      d: `M ${fromNode.x} ${fromNode.y} Q ${cx} ${cy} ${toNode.x} ${toNode.y}`,
      midX: cx,
      midY: cy,
    };
  };

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipPos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div className="relative w-full h-[520px] sm:h-[600px] glass-panel rounded-3xl border border-slate-800/90 overflow-hidden bg-slate-950/80 shadow-2xl flex items-center justify-center p-2">
      
      {/* Background Geographic Grid & Atmosphere */}
      <div className="absolute inset-0 opacity-[0.05] bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-sky-500/5 blur-3xl rounded-full pointer-events-none" />

      {/* SVG Canvas for India Map & Flight Corridors */}
      <svg
        className="w-full h-full max-w-[850px] max-h-[620px] cursor-crosshair select-none"
        viewBox="0 0 850 820"
        onMouseMove={handleMouseMove}
      >
        <defs>
          {/* Node pulse glow */}
          <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#0284c7" stopOpacity="0" />
          </radialGradient>
          <filter id="shadowGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* 1. Curved Flight Corridors */}
        {ROUTE_CONFIGS.map((config) => {
          const fromNode = AIRPORT_NODES[config.from];
          const toNode = AIRPORT_NODES[config.to];
          if (!fromNode || !toNode) return null;

          const pathInfo = createCurvedPath(fromNode, toNode, config.curveOffset);
          const metrics = routeMetricsMap[config.id] || {};
          const isSelected = selectedRouteId === config.id;
          const isHovered = hoveredRoute?.id === config.id;
          const color = getCorridorColor(config.id, metrics);
          const strokeWidth = getStrokeWidth(config.weight);

          return (
            <g key={config.id} className="transition-all duration-300">
              {/* Glow backdrop for selected or hovered corridor */}
              {(isSelected || isHovered) && (
                <path
                  d={pathInfo.d}
                  fill="none"
                  stroke={color}
                  strokeWidth={strokeWidth + 6}
                  strokeOpacity="0.3"
                  strokeLinecap="round"
                />
              )}

              {/* Main Flight Path */}
              <path
                d={pathInfo.d}
                fill="none"
                stroke={color}
                strokeWidth={isSelected ? strokeWidth + 2 : strokeWidth}
                strokeOpacity={isSelected ? 1.0 : isHovered ? 0.9 : 0.75}
                strokeDasharray={mapMode === 'shock' ? '8 4' : 'none'}
                strokeLinecap="round"
                className="cursor-pointer transition-all duration-300"
                onClick={() => onSelectRoute(config.id)}
                onMouseEnter={() => setHoveredRoute({ ...config, ...pathInfo, metrics })}
                onMouseLeave={() => setHoveredRoute(null)}
              />

              {/* Dynamic Animated Flight Pulse along active routes */}
              <circle r={isSelected ? "4" : "3"} fill="#ffffff" filter="url(#shadowGlow)">
                <animateMotion
                  path={pathInfo.d}
                  dur={isSelected ? "3s" : "6s"}
                  repeatCount="indefinite"
                />
              </circle>
            </g>
          );
        })}

        {/* 2. Airport Nodes (IATA Codes + City Labels) */}
        {Object.values(AIRPORT_NODES).map((node) => {
          const isSelectedNode = 
            selectedRouteId && 
            (selectedRouteId.startsWith(node.code) || selectedRouteId.endsWith(node.code));

          return (
            <g key={node.code} transform={`translate(${node.x}, ${node.y})`}>
              {/* Outer pulsing ring */}
              <circle
                r="14"
                fill="url(#nodeGlow)"
                className="animate-ping opacity-30"
              />
              
              {/* Outer border ring */}
              <circle
                r="7"
                fill="#020617"
                stroke={isSelectedNode ? '#38bdf8' : '#64748b'}
                strokeWidth={isSelectedNode ? '2.5' : '1.5'}
              />

              {/* Inner core node */}
              <circle
                r="3.5"
                fill={isSelectedNode ? '#38bdf8' : '#ffffff'}
              />

              {/* City & IATA Label */}
              <text
                x="12"
                y="4"
                fill={isSelectedNode ? '#ffffff' : '#cbd5e1'}
                fontSize="11"
                fontWeight="700"
                fontFamily="JetBrains Mono, monospace"
                className="pointer-events-none drop-shadow-md"
              >
                {node.code} <tspan fill="#64748b" fontSize="9" fontWeight="500">({node.name})</tspan>
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Hover Tooltip */}
      {hoveredRoute && (
        <div
          className="absolute pointer-events-none z-30 p-3 rounded-2xl bg-slate-900/95 border border-sky-500/40 shadow-2xl backdrop-blur-md text-xs space-y-1.5 w-56 font-sans"
          style={{
            left: Math.min(tooltipPos.x + 15, 600),
            top: Math.max(tooltipPos.y - 40, 20),
          }}
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
            <span className="font-extrabold text-white font-mono">{hoveredRoute.id}</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-400/30">
              {selectedWindow}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Airfare Index:</span>
            <span className="font-mono font-bold text-sky-400">
              {hoveredRoute.metrics?.indexValue ?? 100.0}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Current Avg Fare:</span>
            <span className="font-mono font-bold text-white">
              {hoveredRoute.metrics?.avgPrice ? `₹${hoveredRoute.metrics.avgPrice.toLocaleString('en-IN')}` : 'N/A'}
            </span>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px]">
            <span className="text-slate-500">DGCA Monthly Pax:</span>
            <span className="font-mono text-slate-300">
              {hoveredRoute.dgcaPax ? `${(hoveredRoute.dgcaPax / 1000).toFixed(1)}k/mo` : 'N/A'}
            </span>
          </div>

          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-500">Observations:</span>
            <span className="font-mono text-emerald-400">
              {hoveredRoute.metrics?.obsCount ?? 'N/A'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
