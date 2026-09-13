import React, { useState } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import PipelineSection from './components/PipelineSection';
import Dashboard from './components/Dashboard';
import WhitepaperModal from './components/WhitepaperModal';
import Footer from './components/Footer';

export default function App() {
  const [activeView, setActiveView] = useState('overview'); // 'overview' or 'dashboard'
  const [isWhitepaperOpen, setIsWhitepaperOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-sky-500 selection:text-white bg-slate-950">
      
      {/* Navigation Header with View Mode Switcher */}
      <Header 
        activeView={activeView}
        setActiveView={setActiveView}
        onOpenWhitepaper={() => setIsWhitepaperOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-grow pt-16">
        {activeView === 'overview' ? (
          <div>
            <Hero 
              onExploreClick={() => setActiveView('dashboard')}
              onWhitepaperClick={() => setIsWhitepaperOpen(true)}
            />
            <PipelineSection />
          </div>
        ) : (
          <Dashboard />
        )}
      </main>

      {/* Technical Whitepaper Modal */}
      <WhitepaperModal 
        isOpen={isWhitepaperOpen}
        onClose={() => setIsWhitepaperOpen(false)}
      />

      {/* Footer */}
      <Footer 
        onOpenWhitepaper={() => setIsWhitepaperOpen(true)}
      />

    </div>
  );
}
