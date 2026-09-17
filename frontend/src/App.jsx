import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import Sidebar from './components/Sidebar';
import AirfareIntelligencePage from './components/AirfareIntelligencePage';
import Hero from './components/Hero';
import PipelineSection from './components/PipelineSection';
import Dashboard from './components/Dashboard';
import MethodologySection from './components/MethodologySection';

export default function App() {
  // Always start on Landing / Preview Page first
  const [activeView, setActiveView] = useState('landing');

  // Handle transition into dashboard
  const handleExploreDashboard = () => {
    setActiveView('map');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (activeView === 'landing') {
    return (
      <LandingPage 
        onExploreDashboard={handleExploreDashboard} 
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-sky-500 selection:text-white flex">
      
      {/* Persistent Left Sidebar */}
      <Sidebar 
        activeView={activeView}
        setActiveView={setActiveView}
      />

      {/* Scrollable Main Workspace */}
      <main className="flex-grow pl-16 lg:pl-60 min-h-screen transition-all duration-300">
        
        {/* Top Floating Landing Return Bar */}
        <div className="bg-slate-900/60 border-b border-slate-800/80 px-6 py-2 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-2 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-bold">AeroStat Workspace</span>
            <span>•</span>
            <span className="text-sky-400 font-semibold uppercase">{activeView}</span>
          </div>

          <button
            onClick={() => setActiveView('landing')}
            className="hover:text-white text-slate-400 transition-colors font-semibold flex items-center gap-1 cursor-pointer"
          >
            ← Back to Landing Page
          </button>
        </div>

        {activeView === 'map' && (
          <AirfareIntelligencePage />
        )}

        {activeView === 'overview' && (
          <div>
            <Hero 
              onExploreClick={handleExploreDashboard}
            />
            <PipelineSection />
          </div>
        )}

        {(activeView === 'macro' || activeView === 'airlines' || activeView === 'telemetry' || activeView === 'live' || activeView === 'dashboard') && (
          <Dashboard initialTab={activeView === 'dashboard' ? 'macro' : activeView} />
        )}

        {activeView === 'methodology' && (
          <MethodologySection />
        )}

        {(activeView === 'windows' || activeView === 'decomposition' || activeView === 'pipeline') && (
          <PipelineSection />
        )}
      </main>

    </div>
  );
}
