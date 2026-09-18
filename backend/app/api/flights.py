from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.db.connection import get_db_connection
from app.services.scraping_service import scraping_service

router = APIRouter()

class ScrapeRequest(BaseModel):
    origin: str
    destination: str
    windows: List[str]

@router.get("/")
def get_flights(
    route: Optional[str] = Query(None, description="e.g. DEL-BOM"),
    window: Optional[str] = Query(None, description="e.g. T+1"),
    limit: Optional[int] = Query(10000, description="Max records to return")
):
    """
    Fetch flights from the database with optional filtering.
    """
    query = """
        SELECT f.observation_id, f.airline_name, f.flight_number, f.departure_date,
               f.departure_time, f.scrape_timestamp, f.raw_price_displayed, f.advance_booking_window,
               r.origin_airport, r.destination_airport,
               f.base_fare, f.taxes_fees, f.udf, f.gst_amount, f.fuel_surcharge
        FROM flight_observations f
        JOIN routes r ON f.route_id = r.route_id
        WHERE 1=1
    """
    params = []

    if route:
        parts = route.split("-")
        if len(parts) == 2:
            query += " AND r.origin_airport = %s AND r.destination_airport = %s"
            params.extend([parts[0], parts[1]])

    if window:
        query += " AND f.advance_booking_window = %s"
        params.append(window)
        
    query += " ORDER BY f.scrape_timestamp DESC, f.departure_date ASC"
    if limit:
        query += f" LIMIT {int(limit)}"

    results = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                for row in rows:
                    results.append({
                        "observation_id": row[0],
                        "airline_name": row[1],
                        "flight_number": row[2],
                        "departure_date": row[3],
                        "departure_time": str(row[4]) if row[4] else None,
                        "scrape_timestamp": row[5].isoformat() if row[5] else None,
                        "price": float(row[6]) if row[6] else None,
                        "window": row[7],
                        "origin": row[8],
                        "destination": row[9],
                        "base_fare": float(row[10]) if row[10] is not None else None,
                        "taxes_fees": float(row[11]) if row[11] is not None else None,
                        "udf": float(row[12]) if row[12] is not None else None,
                        "gst_amount": float(row[13]) if row[13] is not None else None,
                        "fuel_surcharge": float(row[14]) if row[14] is not None else None,
                    })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return results

def _run_pipeline_background():
    try:
        from app.services.pipeline_service import pipeline_service
        pipeline_service.run_full_pipeline()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to run pipeline after scrape: {e}")


@router.post("/scrape")
def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Triggers the scraping service.
    """
    if not req.windows:
        raise HTTPException(status_code=400, detail="Must provide at least one window")

    try:
        result = scraping_service.run_scrape(req.origin, req.destination, req.windows)

        # Update Route Analytics (index_values) in the background - the full
        # cleaning + Jevons pipeline takes 60-90s+, and running it inline here
        # held the HTTP response open that whole time, which looked like a
        # hung/failed request from the UI (manual scrape trigger timing out).
        if result.get("status") in ["success", "partial_failure"]:
            background_tasks.add_task(_run_pipeline_background)

        # If the overall status is failed, we can still return 200 with failure details 
        # or 500 depending on preference. We'll return 200 with details for visibility.
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
