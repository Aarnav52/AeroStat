import React, { useState } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import PipelineSection from './components/PipelineSection';
import Dashboard from './components/Dashboard';
import WhitepaperModal from './components/WhitepaperModal';
import Footer from './components/Footer';

export default function App() {
  const [isWhitepaperOpen, setIsWhitepaperOpen] = useState(false);

  const scrollToDashboard = () => {
    const el = document.getElementById('dashboard');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToPipeline = () => {
    const el = document.getElementById('pipeline');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      
      {/* Navigation Bar */}
      <Header 
        onOpenWhitepaper={() => setIsWhitepaperOpen(true)}
        onScrollToDashboard={scrollToDashboard}
      />

      {/* Main Content Sections */}
      <main className="flex-grow">
        <Hero 
          onExploreClick={scrollToPipeline}
          onWhitepaperClick={() => setIsWhitepaperOpen(true)}
        />
        <PipelineSection />
        <Dashboard />
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
