import React from 'react';

// Official SVG Brand Logos & Icons for Indian Domestic Airlines
export function AirlineLogo({ name, className = "w-5 h-5", showName = false }) {
  if (!name) return null;
  const cleanName = String(name).trim();
  const lower = cleanName.toLowerCase();

  let logoElement = null;

  if (lower.includes('indigo') || lower.includes('6e')) {
    logoElement = (
      <div className={`rounded-md bg-[#001b69] text-white flex items-center justify-center p-1 shrink-0 ${className}`} title="IndiGo">
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full stroke-current">
          <circle cx="12" cy="12" r="9" strokeWidth="2" stroke="#60a5fa" />
          <path d="M12 3v18M3 12h18" strokeWidth="1.5" stroke="#93c5fd" opacity="0.6" />
          <path d="M7 8l10 8M7 16l10-8" strokeWidth="1.5" stroke="#ffffff" />
        </svg>
      </div>
    );
  } else if (lower.includes('air india express') || lower.includes('ix')) {
    logoElement = (
      <div className={`rounded-md bg-[#e65100] text-white flex items-center justify-center p-1 shrink-0 ${className}`} title="Air India Express">
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
          <path d="M3 17h18l-5-10H8L3 17zm5-8h8l3.5 7H4.5L8 9z" />
          <circle cx="12" cy="12" r="2" fill="#ffffff" />
        </svg>
      </div>
    );
  } else if (lower.includes('air india') || lower.includes('ai')) {
    logoElement = (
      <div className={`rounded-md bg-[#b71c1c] text-amber-300 flex items-center justify-center p-1 shrink-0 ${className}`} title="Air India">
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
          <circle cx="12" cy="12" r="9" fill="#d32f2f" />
          <path d="M6 15c4-1 8-6 12-7-3 4-7 8-12 7z" fill="#fbc02d" />
          <circle cx="15" cy="8" r="1.5" fill="#ffffff" />
        </svg>
      </div>
    );
  } else if (lower.includes('akasa') || lower.includes('qp')) {
    logoElement = (
      <div className={`rounded-md bg-[#ff6f00] text-white flex items-center justify-center p-1 shrink-0 ${className}`} title="Akasa Air">
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full stroke-current stroke-[2.5]">
          <path d="M4 19L12 4l8 15" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M8 13h8" strokeLinecap="round" stroke="#ffe0b2" />
        </svg>
      </div>
    );
  } else if (lower.includes('spicejet') || lower.includes('sg')) {
    logoElement = (
      <div className={`rounded-md bg-[#d84315] text-amber-200 flex items-center justify-center p-1 shrink-0 ${className}`} title="SpiceJet">
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
          <circle cx="6" cy="6" r="2" />
          <circle cx="12" cy="6" r="2.5" />
          <circle cx="18" cy="6" r="2" />
          <circle cx="9" cy="12" r="2.5" />
          <circle cx="15" cy="12" r="2" />
          <circle cx="12" cy="18" r="3" />
        </svg>
      </div>
    );
  } else if (lower.includes('vistara') || lower.includes('uk')) {
    logoElement = (
      <div className={`rounded-md bg-[#4a148c] text-amber-300 flex items-center justify-center p-1 shrink-0 ${className}`} title="Vistara">
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
          <path d="M12 2l2.5 7.5H22l-6 4.5 2.5 7.5-6.5-5-6.5 5 2.5-7.5-6-4.5h7.5z" />
        </svg>
      </div>
    );
  } else {
    const initials = cleanName
      .split(' ')
      .map(part => part[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();

    logoElement = (
      <div className={`rounded-md bg-slate-800 border border-slate-700 text-sky-400 font-bold font-mono text-[10px] flex items-center justify-center shrink-0 ${className}`} title={cleanName}>
        {initials || 'AI'}
      </div>
    );
  }

  if (showName) {
    return (
      <div className="inline-flex items-center space-x-2">
        {logoElement}
        <span className="font-semibold text-slate-200">{cleanName}</span>
      </div>
    );
  }

  return logoElement;
}
