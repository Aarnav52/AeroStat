// APEX-IND Simulated Real-Time Data Engine for Airfare Price Index & Analytics

export const HERO_STATS = [
  { label: 'APEX-IND Index Value', value: '168.45', change: '+1.42%', period: '7d avg', status: 'up' },
  { label: 'Price Volatility Index', value: '0.0394', change: '-0.18%', period: '7d avg', status: 'down' },
  { label: 'Advance Window Coverage', value: '45 Days', subtext: 'T-0 to T-45 Buckets', status: 'neutral' },
  { label: 'Direct Route Ratio', value: '89.4%', subtext: '120 Metro & Non-Metro Corridors', status: 'neutral' }
];

export const LIVE_TICKER_FEED = [
  { id: 1, route: 'DEL → BOM', airline: 'IndiGo', code: '6E-2041', rawFare: 5240, cleanFare: 4850, change: '+2.1%', status: 'Normal', time: '12s ago' },
  { id: 2, route: 'BOM → BLR', airline: 'Air India', code: 'AI-609', rawFare: 4100, cleanFare: 3420, change: '-1.2%', status: 'Cleaned', time: '18s ago' },
  { id: 3, route: 'DEL → CCU', airline: 'Vistara', code: 'UK-707', rawFare: 5890, cleanFare: 5100, change: '+0.5%', status: 'Normal', time: '34s ago' },
  { id: 4, route: 'BLR → DEL', airline: 'Akasa Air', code: 'QP-1102', rawFare: 6950, cleanFare: 6200, change: '+3.4%', status: 'Promo Filtered', time: '42s ago' },
  { id: 5, route: 'HYD → BOM', airline: 'SpiceJet', code: 'SG-432', rawFare: 4300, cleanFare: 3890, change: '-0.8%', status: 'Normal', time: '55s ago' },
  { id: 6, route: 'MAA → DEL', airline: 'IndiGo', code: '6E-512', rawFare: 6100, cleanFare: 5650, change: '+1.9%', status: 'Cleaned', time: '1m ago' },
];

export const BOOKING_WINDOWS = [
  { bucket: 'T-0 (Same Day)', avgPrice: 9450, indexWeight: '12%', volatility: '0.082', trend: '+4.8%' },
  { bucket: 'T-3 (1-3 Days)', avgPrice: 7800, indexWeight: '22%', volatility: '0.054', trend: '+2.1%' },
  { bucket: 'T-7 (4-7 Days)', avgPrice: 6150, indexWeight: '28%', volatility: '0.038', trend: '+1.2%' },
  { bucket: 'T-14 (8-14 Days)', avgPrice: 5100, indexWeight: '18%', volatility: '0.024', trend: '-0.4%' },
  { bucket: 'T-30 (15-30 Days)', avgPrice: 4350, indexWeight: '12%', volatility: '0.019', trend: '-1.1%' },
  { bucket: 'T-45 (31-45 Days)', avgPrice: 3950, indexWeight: '8%', volatility: '0.015', trend: '-0.2%' },
];

// Historical Index Time Series (Daily points over selected range)
export const generateTimeSeriesData = (range = '90D', shockFactor = 1.0) => {
  const pointsCount = range === '7D' ? 7 : range === '30D' ? 30 : range === '90D' ? 90 : range === '1Y' ? 365 : 180;
  const data = [];
  let baseGEKS = 152.0 * shockFactor;
  let baseLaspeyres = 152.0 * shockFactor;
  let baseCPI = 148.5;
  let baseATF = 140.0;
  
  const today = new Date();
  
  for (let i = pointsCount; i >= 0; i--) {
    const d = new Date();
    d.setDate(today.getDate() - i);
    
    // Add realistic market dynamics with chain drift in Laspeyres
    const randomNoise = (Math.random() - 0.48) * 0.9 * shockFactor;
    const macroTrend = 0.15; // gradual inflation
    
    baseGEKS += macroTrend + randomNoise;
    // Laspeyres exhibits upward chain drift over time
    baseLaspeyres += macroTrend + randomNoise + 0.045;
    baseCPI += 0.08 + (Math.random() - 0.49) * 0.2;
    baseATF += (Math.random() - 0.45) * 1.2;
    
    data.push({
      date: d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
      fullDate: d.toISOString().split('T')[0],
      geksIndex: parseFloat(baseGEKS.toFixed(2)),
      laspeyresIndex: parseFloat(baseLaspeyres.toFixed(2)),
      mospiCPI: parseFloat(baseCPI.toFixed(2)),
      atfBenchmark: parseFloat(baseATF.toFixed(2)),
      avgFare: Math.round(baseGEKS * 32.1),
      volatility: parseFloat((0.035 + Math.random() * 0.01).toFixed(4))
    });
  }
  return data;
};

export const TOP_ROUTES_DATA = [
  { rank: 1, route: 'DEL - BOM', name: 'Delhi ↔ Mumbai', volume: '18.4%', avgFare: 5420, change7d: '+2.4%', status: 'High Demand' },
  { rank: 2, route: 'BOM - BLR', name: 'Mumbai ↔ Bengaluru', volume: '14.2%', avgFare: 4150, change7d: '-0.9%', status: 'Stable' },
  { rank: 3, route: 'DEL - BLR', name: 'Delhi ↔ Bengaluru', volume: '12.8%', avgFare: 6890, change7d: '+3.1%', status: 'High Demand' },
  { rank: 4, route: 'DEL - CCU', name: 'Delhi ↔ Kolkata', volume: '9.6%', avgFare: 5210, change7d: '+0.4%', status: 'Stable' },
  { rank: 5, route: 'HYD - BOM', name: 'Hyderabad ↔ Mumbai', volume: '8.1%', avgFare: 3950, change7d: '-1.4%', status: 'Discounted' },
  { rank: 6, route: 'MAA - DEL', name: 'Chennai ↔ Delhi', volume: '7.5%', avgFare: 5980, change7d: '+1.8%', status: 'Stable' },
];

export const AIRLINE_BREAKDOWN = [
  { name: 'IndiGo', code: '6E', marketShare: '61.4%', indexValue: 166.2, change7d: '+1.1%', fleetActive: 360 },
  { name: 'Air India Group (incl. Vistara)', code: 'AI/UK', marketShare: '28.2%', indexValue: 172.8, change7d: '+1.9%', fleetActive: 220 },
  { name: 'Akasa Air', code: 'QP', marketShare: '4.8%', indexValue: 159.4, change7d: '-0.5%', fleetActive: 24 },
  { name: 'SpiceJet', code: 'SG', marketShare: '4.1%', indexValue: 164.1, change7d: '+0.2%', fleetActive: 28 },
  { name: 'Others (Alliance, AIX)', code: 'OTH', marketShare: '1.5%', indexValue: 161.0, change7d: '+0.0%', fleetActive: 18 }
];

export const DEDUPLICATION_STATS = {
  rawScrapedCount: '4,218,940 Fares/Day',
  cleanIndexedCount: '3,619,849 Clean Fares',
  ancillaryFilteredPercent: '14.2%',
  ghostInventoriesRemoved: '99.8%',
  duplicateFaresMerged: '599,091'
};

// Simulation presets for live testing
export const SIMULATION_PRESETS = [
  { id: 'normal', label: 'Baseline Market', shockFactor: 1.0, desc: 'Normal domestic aviation supply and demand.' },
  { id: 'diwali', label: 'Festive Surge (+18%)', shockFactor: 1.18, desc: 'Diwali & festival demand surge across trunk corridors.' },
  { id: 'monsoon', label: 'Monsoon Discount (-12%)', shockFactor: 0.88, desc: 'Seasonal off-peak pricing across regional routes.' },
  { id: 'fuel_spike', label: 'ATF Fuel Spike (+24%)', shockFactor: 1.24, desc: 'Crude price escalation pushing airline fuel surcharges.' }
];

// Anomaly Logs Simulation
export const ANOMALY_LOGS = [
  { id: 'AN-809', time: '14:22:01', route: 'DEL-BOM', type: 'Ghost Inventory', rawFare: '₹1,200', action: 'Purged', severity: 'High' },
  { id: 'AN-810', time: '14:25:40', route: 'BOM-BLR', type: 'Ancillary Surcharge', rawFare: '₹5,800', action: 'Stripped ₹650', severity: 'Medium' },
  { id: 'AN-811', time: '14:28:15', route: 'DEL-CCU', type: 'Promo Glitch', rawFare: '₹99', action: 'Filtered', severity: 'High' },
  { id: 'AN-812', time: '14:31:02', route: 'HYD-DEL', type: 'Duplicate Scrape', rawFare: '₹4,350', action: 'Deduplicated', severity: 'Low' }
];
