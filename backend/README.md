# Airfare Price Index Backend (SIH Prototype)

## Stack
- **Python 3.14** · FastAPI · Uvicorn
- **PostgreSQL** (Supabase)
- **SerpApi** – Google Flights engine
- **Vite + React** frontend (separate)

---

## Project Structure
```
backend/
├── .env                          ← credentials (never commit)
├── requirements.txt
├── run_sweep_t1.bat              ← Task Scheduler entrypoint, T+1 (every 6h)
├── run_sweep_t7.bat              ← Task Scheduler entrypoint, T+7 (daily)
├── run_sweep_t15.bat             ← Task Scheduler entrypoint, T+15 (every 36h)
├── run_sweep_t30.bat             ← Task Scheduler entrypoint, T+30 (every 3 days)
├── run_sweep_t45.bat             ← Task Scheduler entrypoint, T+45 (every 4 days)
├── logs/                         ← sweep logs (gitignored)
├── test_polite_fetcher.py        ← 25 unit tests, fake transport, no real network
├── scripts/
│   └── check_db.py               ← manual schema/data inspector (standalone, no app import)
└── app/
    ├── config.py                 ← loads .env
    ├── main.py                   ← FastAPI app + CORS, mounts routers below
    ├── db/
    │   ├── connection.py         ← psycopg2 context manager
    │   └── queries.py            ← INSERT with same-day dedup guard +
    │                                fee-decomposition hook
    ├── scraper/
    │   ├── polite_fetcher.py     ← compliance gate every scraper goes through
    │   │                            (robots.txt, bot-challenge detection,
    │   │                            per-host rate limit, circuit breaker)
    │   ├── serpapi_client.py     ← SerpApi Google Flights client
    │   ├── flight_parser.py      ← SerpApi JSON → DB dict parser
    │   ├── direct_scrapers.py    ← Akasa Air / SpiceJet, routed through
    │   │                            PoliteFetcher, any route/date
    │   ├── run_all_scrapers.py   ← full-sweep entrypoint (--window T+1/T+7/
    │   │                            T+15/T+30/T+45, --limit N); what the
    │   │                            .bat files call. run_full_sweep() is
    │   │                            two phases: SerpApi across all routes
    │   │                            first (fast, seconds/route), then the
    │   │                            direct Playwright scrapers across all
    │   │                            routes (slow, flaky) — so the slow
    │   │                            scrapers on one route never block the
    │   │                            fast SerpApi call on the next. Each
    │   │                            phase runs the index pipeline
    │   │                            afterward if it inserted rows.
    │   └── scrape_akasa_live.py, scrape_spicejet_live.py,
    │       demo_polite_fetcher_live.py
    │                            ← original single-route demo scripts,
    │                               superseded by direct_scrapers.py +
    │                               run_all_scrapers.py but kept as minimal
    │                               standalone examples of the pattern
    ├── services/
    │   ├── scraping_service.py   ← orchestrates the SerpApi scrape for a
    │   │                            requested set of booking windows
    │   ├── fee_decomposition.py  ← tariff-schedule-derived base_fare/
    │   │                            taxes_fees/udf/gst_amount/fuel_surcharge
    │   └── index_service.py      ← ⚠ SEE "Jevons Index" SECTION BELOW —
    │                                this is a placeholder, not the real engine
    └── api/
        ├── flights.py             ← GET /flights/  POST /flights/scrape
        ├── routes.py              ← GET /routes/
        ├── index.py               ← GET /index/  GET /index/summary
        │                              (currently backed by the placeholder
        │                              above, not jevons_engine/)
        └── analyst.py             ← GET/POST /analyst/* — see "AeroStat
                                       Analyst" section below
```

The real statistics engine, `jevons_engine/jevons_engine_cloud.py`, lives at
the repo root (sibling of `backend/`, not inside it) — it's owned/maintained
separately and is not yet wired to the API above (see below).

`agents/` (repo root, sibling of `backend/`) holds the analyst's deterministic
tool layer that `api/analyst.py` calls into:
```
agents/
├── __init__.py
└── tools/
    ├── registry.py                ← TOOL_REGISTRY (name → schema + handler),
    │                                  get_tool_schemas(), dispatch_tool()
    ├── cpi_tools.py                ← get_latest_cpi/get_cpi_history/
    │                                  compare_cpi_periods, reads index_values
    ├── analysis_tools.py           ← route/airline/booking-window/cabin
    │                                  breakdowns, reads cleaned_observations_table
    └── quality_and_meta_tools.py   ← data quality summary, supporting
                                       observations (evidence), route lookups
```
Every tool here is deterministic (plain DB queries) — Groq only ever picks
*which* registered tool to call and with what arguments; it never computes
a number itself. `tests/test_analyst.py` (repo root) covers this layer.

---

## Environment Variables

Create `backend/.env`:
```env
DATABASE_URL=postgresql://...   # Supabase connection string
SERPAPI_KEY=...                 # SerpApi API key
GROQ_API_KEY=...                # Groq API key, required for /analyst/* endpoints
                                 # (AeroStat Analyst chat/tool-calling). Backend
                                 # still starts and every other endpoint still
                                 # works without it - only /analyst/* requests
                                 # fail with a clean error if it's unset.
GROQ_MODEL=openai/gpt-oss-120b  # optional, this is the default
GROQ_MAX_TOOL_ROUNDS=8          # optional, this is the default
```

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

---

## How to Run

### 1 — Backend

```bash
cd backend
pip3 install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend is live at: http://localhost:8000
Swagger docs at:    http://localhost:8000/docs

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is live at: http://localhost:5173

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Backend health check |
| GET | `/routes/` | All active routes |
| GET | `/flights/` | Stored observations (filter: `?route=DEL-BOM&window=T+1`) |
| POST | `/flights/scrape` | Trigger scrape `{"origin":"DEL","destination":"BOM","windows":["T+1","T+30"]}` |
| GET | `/index/` | Jevons index series (`?route=DEL-BOM&window=T+1`) |
| GET | `/index/summary` | Index for all windows (`?route=DEL-BOM`) |
| GET | `/analyst/tools` | List registered analyst tool schemas |
| POST | `/analyst/tools/execute` | Run one named tool directly, bypassing Groq `{"tool_name":"...","arguments":{...}}` |
| POST | `/analyst/query` | Ask a natural-language question; Groq picks tools, returns `{answer, key_findings, evidence, limitations, tool_calls}`. Requires `GROQ_API_KEY`. Frontend: `AnalystChat.jsx` (Sidebar → "AeroStat Analyst"). |
| GET | `/analyst/cpi/latest` | Latest index value (`?index_type=national\|route\|elementary&route_id=...&advance_booking_window=T+1`) |
| GET | `/analyst/cpi/history` | Index time series, same filters as above |
| POST | `/analyst/cpi/compare` | Compare two index dates `{"current_date":"...","previous_date":"...",...}` |
| GET | `/analyst/analysis/routes` \| `/airlines` \| `/booking-windows` \| `/cabins` | Price breakdowns by that dimension |
| GET | `/analyst/quality` | Data quality/coverage summary |
| GET | `/analyst/observations` | Raw supporting flight observations (evidence for an analyst answer) |
| GET | `/analyst/routes/{route_id}` | Human-readable metadata for one route |

---

## Data Flow

Each booking window is swept on its own Task Scheduler cadence, tighter for
windows closer to departure (where dynamic pricing moves fastest) and wider
for windows further out (where fares are far more stable day-to-day, so
polling them as often just adds unnecessary scrape volume):

| Window | Cadence |
|--------|---------|
| T+1  | every 6h |
| T+7  | daily |
| T+15 | every 36h |
| T+30 | every 3 days |
| T+45 | every 4 days |

These triggers live in Windows Task Scheduler, not in this repo (the `.bat`
files themselves don't encode a schedule) - check/update them via
`Get-ScheduledTask -TaskName "AeroStat Scrape T+*"` in PowerShell.

Two collection paths, one shared write path (see `SIH26056_APIx_
Architecture_and_Pipelines.md` one level above the repo for full diagrams):

```
Windows Task Scheduler (run_sweep_t1/t7/t15/t30/t45.bat)
        ↓
  run_all_scrapers.py  (run_full_sweep — every active route, two phases)
        Phase 1 (fast, all routes) ──→ scraping_service.py → serpapi_client.py → flight_parser.py
        Phase 2 (slow, all routes) ──→ direct_scrapers.py → polite_fetcher.py → Akasa/SpiceJet sites
        ↓                                   (both paths converge here)
  queries.py:
    1. same-IST-day dedup check (skip already-scraped flight+date+window)
    2. fee_decomposition.py (fill base_fare/taxes/udf/gst if a tariff
       schedule exists for this airline+station — never fabricated)
    3. INSERT INTO flight_observations
        ↓
  Supabase PostgreSQL (apix(SIH))
        ↓
  FastAPI endpoints  (serve to frontend)
        ↓
  LiveDataPanel.jsx / Dashboard.jsx / AirlineAnalytics.jsx
```

---

## Jevons Index

**⚠ `index_service.py` is a placeholder, not the real Jevons/GEKS-Jevons
engine.** Despite its name and docstring, `calculate_jevons_index()` does
NOT compute a geometric mean of price relatives — it computes
`(AVG(price today) / AVG(price on base date)) × 100`, a simple ratio of
arithmetic means. (It even defines an unused `_geometric_mean()` helper
that nothing calls — dead code, not wired in.) This is what `GET /index/`
currently returns, and what the dashboard's "AeroStat GEKS" panel displays.

The real, correctly-implemented engine is `jevons_engine/
jevons_engine_cloud.py` (repo root, not under `backend/`) — it genuinely
computes `exp(mean(log(price_relative))) * 100` per the Jevons formula,
with a route-level and national rollup on top. It reads from
`cleaned_observations_table` and writes to an `index_values` table. **It is
not yet wired to `GET /index/`** — that reconnection (fix the table schema
so the engine's own output actually persists, point this API at it instead
of `index_service.py`) is a known, open, in-progress item, not a
methodology gap. Don't present the current `/index/` output as GEKS-Jevons
without this caveat.

---

## Notes

- `lead_time_days` is a **PostgreSQL generated column** — Python never writes it
- `cabin_class` must be one of: `economy`, `premium_economy`, `business`
- `source_type` must be one of: `airline_direct`, `ota`, `api`
- Duplicate guard is two-layered: a DB unique constraint
  (`ON CONFLICT (route_id, source_id, flight_number, departure_date,
  scrape_timestamp) DO NOTHING`) plus an application-level same-IST-day
  check in `insert_observations()` — the DB constraint alone can't catch
  two sweep runs minutes apart, since `scrape_timestamp` is fresh every
  call; the app-level check is what actually prevents that.
- All timestamps use `Asia/Kolkata` timezone

---

## Adding More Routes Later

In `scraping_service.py`, add entries to `city_lookup`:
```python
self.city_lookup = {
    "DEL": "Delhi",
    "BOM": "Mumbai",
    "BLR": "Bengaluru",   # add more here
    "CCU": "Kolkata",
}
```
Then POST to `/flights/scrape` with the new route.
