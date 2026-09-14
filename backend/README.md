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
├── .env                        ← credentials (never commit)
├── requirements.txt
├── check_db.py                 ← one-time schema inspector
└── app/
    ├── config.py               ← loads .env
    ├── main.py                 ← FastAPI app + CORS
    ├── db/
    │   ├── connection.py       ← psycopg2 context manager
    │   └── queries.py          ← SQL: sources / routes / observations
    ├── scraper/
    │   ├── serpapi_client.py   ← SerpApi Google Flights client
    │   └── flight_parser.py    ← JSON → DB dict parser
    ├── services/
    │   ├── scraping_service.py ← orchestrates T+1 / T+30 scrape
    │   └── index_service.py    ← Jevons price index calculation
    └── api/
        ├── flights.py          ← GET /flights/  POST /flights/scrape
        ├── routes.py           ← GET /routes/
        └── index.py            ← GET /index/  GET /index/summary
```

---

## Environment Variables

Create `backend/.env`:
```env
DATABASE_URL=postgresql://...   # Supabase connection string
SERPAPI_KEY=...                 # SerpApi API key
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

---

## Data Flow

```
SerpApi Google Flights
        ↓
  serpapi_client.py  (fetch raw JSON)
        ↓
  flight_parser.py   (parse → dict)
        ↓
  scraping_service.py (T+1 / T+30 dates, orchestration)
        ↓
  queries.py         (INSERT INTO flight_observations)
        ↓
  Supabase PostgreSQL
        ↓
  FastAPI endpoints  (serve to frontend)
        ↓
  LiveDataPanel.jsx  (React dashboard tab)
```

---

## Jevons Index

- Implemented in `app/services/index_service.py`
- Fully decoupled from scraper — statistical team can modify freely
- Formula: **J = (P_current / P_base) × 100**
- Base = earliest available scrape date (auto-detected)
- Index grows richer as more daily scrapes accumulate

---

## Notes

- `lead_time_days` is a **PostgreSQL generated column** — Python never writes it
- `cabin_class` must be one of: `economy`, `premium_economy`, `business`
- `source_type` must be one of: `airline_direct`, `ota`, `api`
- Duplicate guard: `ON CONFLICT (route_id, source_id, flight_number, departure_date, scrape_timestamp) DO NOTHING`
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
