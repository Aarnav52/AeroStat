// API Service — connects the frontend to the FastAPI backend.
// Base URL is controlled via the VITE_API_URL environment variable.

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function apiFetch(path, options = {}) {
  const cacheKey = `aerostat_cache_${path}`;
  
  try {
    const res = await fetch(`${API_BASE}${path}`, options);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    
    // Only cache GET requests that are successful
    if (!options.method || options.method === 'GET') {
      try {
        localStorage.setItem(cacheKey, JSON.stringify({
          data,
          _cached_at: new Date().toISOString()
        }));
      } catch (e) {
        // Ignore localStorage quota errors
      }
    }
    return data;
  } catch (error) {
    // On network failure, try to serve from cache
    if (!options.method || options.method === 'GET') {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        console.warn(`[Network Failure] Serving ${path} from cache`);
        const parsed = JSON.parse(cached);
        // Inject the cached timestamp so the frontend can detect staleness
        return {
          ...parsed.data,
          _is_cached: true,
          _cached_at: parsed._cached_at
        };
      }
    }
    throw error;
  }
}

// GET /health
export const fetchHealth = () => apiFetch('/health');

// GET /routes/
export const fetchRoutes = () => apiFetch('/routes/');

// GET /flights/?route=DEL-BOM&window=T+1
export const fetchFlights = (route, window) => {
  const params = new URLSearchParams();
  if (route) params.set('route', route);
  if (window) params.set('window', window);
  return apiFetch(`/flights/?${params.toString()}`);
};

// POST /flights/scrape
export const triggerScrape = (origin, destination, windows) =>
  apiFetch('/flights/scrape', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ origin, destination, windows }),
  });

// GET /index/?route=DEL-BOM&window=T+1
export const fetchIndex = (route, window) => {
  const params = new URLSearchParams({ route, window });
  return apiFetch(`/index/?${params.toString()}`);
};

// GET /index/summary?route=DEL-BOM
export const fetchIndexSummary = (route) =>
  apiFetch(`/index/summary?route=${route}`);
