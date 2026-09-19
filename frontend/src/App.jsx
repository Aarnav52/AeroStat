import React, { useState } from 'react';
import { Sparkles } from 'lucide-react';
import LandingPage from './components/LandingPage';
import Sidebar from './components/Sidebar';
import AirfareIntelligencePage from './components/AirfareIntelligencePage';
import Hero from './components/Hero';
import PipelineSection from './components/PipelineSection';
import Dashboard from './components/Dashboard';
import AnalystChat from './components/AnalystChat';
import MethodologySection from './components/MethodologySection';
import VantaClouds from './components/VantaClouds';

export default function App() {
  // Always start on Landing / Preview Page first
  const [activeView, setActiveView] = useState('landing');
  // Popup, not a tab - reachable from every view via the sidebar trigger
  const [analystOpen, setAnalystOpen] = useState(false);

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

      {/* AeroStat Analyst launcher - a floating icon, not a tab, so it never
          takes space from or obstructs the sidebar's nav items or footer */}
      <button
        onClick={() => setAnalystOpen(true)}
        title="AeroStat Analyst"
        className="fixed bottom-24 left-4 lg:left-6 z-[60] w-12 h-12 lg:w-14 lg:h-14 rounded-full bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/30 hover:scale-105 active:scale-95 transition-transform"
      >
        <Sparkles className="w-5 h-5 lg:w-6 lg:h-6" />
      </button>

      {analystOpen && (
        <AnalystChat onClose={() => setAnalystOpen(false)} />
      )}

    </div>
  );
}
