// API Service — connects the frontend to the FastAPI backend.
// Base URL is controlled via the VITE_API_URL environment variable.

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
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

// POST /analyst/query
export const postAnalystQuery = (question) =>
  apiFetch('/analyst/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
