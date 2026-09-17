import React, { useEffect, useRef, useState } from 'react';

/**
 * VantaClouds — loads the REAL Vanta.js CLOUDS WebGL effect via CDN scripts.
 *
 * Why CDN instead of npm?
 *   Vanta.js v0.5.x was built against Three.js r128.
 *   The project has three@0.186 in package.json which is incompatible.
 *   Loading r128 from CDN guarantees the effect works.
 */

function loadScript(src) {
  return new Promise((resolve, reject) => {
    // Don't load twice
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      if (existing.dataset.loaded === 'true') {
        resolve();
      } else {
        existing.addEventListener('load', resolve);
        existing.addEventListener('error', reject);
      }
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => {
      script.dataset.loaded = 'true';
      resolve();
    };
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

const THREE_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
const VANTA_CDN = 'https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.clouds.min.js';

export default function VantaClouds({ children, className = '' }) {
  const vantaRef = useRef(null);
  const effectRef = useRef(null);
  const [ready, setReady] = useState(false);

  // 1. Load CDN scripts once
  useEffect(() => {
    let cancelled = false;

    async function loadLibs() {
      try {
        // Three.js r128 MUST load first
        await loadScript(THREE_CDN);
        // Then Vanta Clouds
        await loadScript(VANTA_CDN);
        if (!cancelled) setReady(true);
      } catch (err) {
        console.error('[VantaClouds] Failed to load CDN scripts:', err);
      }
    }

    loadLibs();
    return () => { cancelled = true; };
  }, []);

  // 2. Initialize the REAL VANTA.CLOUDS effect once scripts are loaded
  useEffect(() => {
    if (!ready || !vantaRef.current) return;
    if (effectRef.current) return; // already initialized

    // Safety: wait a tick for scripts to fully register on window
    const timer = setTimeout(() => {
      if (!window.VANTA || !window.VANTA.CLOUDS) {
        console.error('[VantaClouds] window.VANTA.CLOUDS not available after script load');
        return;
      }

      try {
        effectRef.current = window.VANTA.CLOUDS({
          el: vantaRef.current,

          // Controls
          mouseControls: true,
          touchControls: true,
          gyroControls: false,

          // Sizing
          minHeight: 200,
          minWidth: 200,
          scale: 3,
          scaleMobile: 12,

          // EXACT user-specified color parameters (decimal integers)
          backgroundColor: 16777215,   // #FFFFFF  — white
          skyColor: 2447234,           // #255382
          cloudColor: 11387358,        // #ADBA5E → warm cloud tone
          cloudShadowColor: 1062495,   // #1037DF
          sunColor: 15902801,          // #F2C051
          sunGlareColor: 16737843,     // #FF8633
          sunlightColor: 16093237,     // #F59E25

          speed: 1
        });

        console.log('[VantaClouds] ✓ REAL Vanta.CLOUDS WebGL effect initialized');
      } catch (err) {
        console.error('[VantaClouds] Initialization error:', err);
      }
    }, 100);

    return () => {
      clearTimeout(timer);
      if (effectRef.current && typeof effectRef.current.destroy === 'function') {
        try { effectRef.current.destroy(); } catch (e) { /* cleanup */ }
        effectRef.current = null;
      }
    };
  }, [ready]);

  return (
    <div className="relative w-full min-h-screen overflow-hidden">
      {/* Layer 0 — Vanta Clouds live WebGL background */}
      <div
        id="vanta-clouds-bg"
        ref={vantaRef}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 0,
          pointerEvents: 'auto',
        }}
      />

      {/* Layer 1 — Very subtle readability overlay (keeps text readable on moving clouds) */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 1,
          background: 'rgba(255,255,255,0.10)',
          pointerEvents: 'none',
        }}
      />

      {/* Foreground Content */}
      <div className={`relative w-full min-h-screen ${className}`} style={{ zIndex: 10, color: '#0f172a' }}>
        {children}
      </div>
    </div>
  );
}
