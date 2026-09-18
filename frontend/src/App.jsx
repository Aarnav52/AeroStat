import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import Sidebar from './components/Sidebar';
import AirfareIntelligencePage from './components/AirfareIntelligencePage';
import Hero from './components/Hero';
import PipelineSection from './components/PipelineSection';
import Dashboard from './components/Dashboard';
import MethodologySection from './components/MethodologySection';
import VantaClouds from './components/VantaClouds';

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
