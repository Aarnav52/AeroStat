import React from 'react';
import useNetworkStatus from '../hooks/useNetworkStatus';

export default function NetworkStatusIndicator() {
  const { status, lastChecked } = useNetworkStatus();

  if (status === 'ONLINE') {
    return (
      <div className="flex items-center space-x-2" title={`Last checked: ${lastChecked.toLocaleTimeString()}`}>
        <span className="w-2 h-2 rounded-full bg-[#1D7F54] animate-pulse shadow-[0_0_8px_rgba(29,127,84,0.6)]" />
        <span className="font-semibold text-slate-300 font-mono text-[11px] tracking-wide">System Live</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2" title={`Backend unreachable. Last checked: ${lastChecked.toLocaleTimeString()}`}>
      <span className="w-2 h-2 rounded-full border-2 border-slate-500" />
      <span className="font-semibold text-slate-500 font-mono text-[11px] tracking-wide">OFFLINE</span>
    </div>
  );
}
