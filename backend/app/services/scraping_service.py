import logging
from datetime import datetime, timedelta
import pytz

from app.scraper.serpapi_client import serpapi_client
from app.scraper.flight_parser import FlightParser
from app.db.connection import get_db_connection
from app.db.queries import get_or_create_source, get_or_create_route, insert_observations

logger = logging.getLogger(__name__)

import json
import os
import traceback

PENDING_QUEUE_FILE = "pending_observations_queue.json"

def _load_pending_queue():
    if not os.path.exists(PENDING_QUEUE_FILE):
        return []
    try:
        with open(PENDING_QUEUE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load pending queue: {e}")
        return []

def _save_pending_queue(queue):
    try:
        with open(PENDING_QUEUE_FILE, "w") as f:
            json.dump(queue, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save pending queue: {e}")

class ScrapingService:
    def __init__(self):
        self.timezone = pytz.timezone("Asia/Kolkata")
        self.parser = FlightParser()
        self.city_lookup = {
            "DEL": "Delhi",
            "BOM": "Mumbai"
        }

    def retry_pending_queue(self, conn):
        """Attempts to insert previously failed observations from the local JSON queue."""
        queue = _load_pending_queue()
        if not queue:
            return

        logger.info(f"Attempting to upload {len(queue)} pending observation batches from local queue.")
        remaining_queue = []
        total_inserted = 0
        total_skipped = 0

        for item in queue:
            try:
                # Convert string timestamps back to datetime if necessary
                # (FlightParser logic and DB insertion might be flexible, but better safe)
                inserted, skipped = insert_observations(conn, item["observations"], item["route_id"], item["source_id"])
                total_inserted += inserted
                total_skipped += skipped
                logger.info(f"Pending batch uploaded: {inserted} inserted, {skipped} skipped.")
            except Exception as e:
                logger.error(f"Pending batch upload failed again: {e}")
                remaining_queue.append(item)

        _save_pending_queue(remaining_queue)
        logger.info(f"Pending queue retry complete. {len(remaining_queue)} batches still pending. {total_inserted} inserted.")

    def calculate_date_for_window(self, window: str) -> str:
        today = datetime.now(self.timezone)
        
        if window == "T+1":
            target = today + timedelta(days=1)
        elif window == "T+7":
            target = today + timedelta(days=7)
        elif window == "T+15":
            target = today + timedelta(days=15)
        elif window == "T+30":
            target = today + timedelta(days=30)
        elif window == "T+45":
            target = today + timedelta(days=45)
        elif window.startswith("T+") and window[2:].isdigit():
            target = today + timedelta(days=int(window[2:]))
        else:
            raise ValueError(f"Unsupported booking window: {window}")
            
        return target.strftime("%Y-%m-%d")

    def run_scrape(self, origin: str, destination: str, windows: list) -> dict:
        results = {
            "route": f"{origin}-{destination}",
            "windows": windows,
            "status": "success",
            "details": []
        }
        
        origin_city = self.city_lookup.get(origin, "Unknown")
        destination_city = self.city_lookup.get(destination, "Unknown")

        try:
            conn = get_db_connection()
            # Attempt to retry pending items before starting new scrapes
            self.retry_pending_queue(conn)
        except Exception as e:
            logger.error(f"Database connection failed entirely. Unable to proceed with normal scraping workflow: {e}")
            return {"status": "failed", "error": "DATABASE_ERROR", "message": "Supabase unreachable, aborting scrape"}

        with conn:
            source_id = get_or_create_source(conn, "Google Flights SerpApi", "api")
            route_id = get_or_create_route(conn, origin, destination, origin_city, destination_city)
            
            for window in windows:
                window_result = {
                    "window": window,
                    "target_date": None,
                    "flights_found": 0,
                    "rows_inserted": 0,
                    "error": None
                }
                
                try:
                    target_date = self.calculate_date_for_window(window)
                    window_result["target_date"] = target_date
                    
                    logger.info(f"Starting scrape for {origin}-{destination} on {target_date} ({window})")
                    
                    api_response = serpapi_client.get_flights(origin, destination, target_date)
                    
                    if not api_response["success"]:
                        logger.error(f"API Error (NETWORK/SOURCE) for {window}: {api_response['error']}")
                        window_result["error"] = api_response["error"]
                        results["status"] = "partial_failure"
                        results["details"].append(window_result)
                        continue
                        
                    observations = self.parser.parse_flights(api_response["data"], target_date, window)
                    window_result["flights_found"] = len(observations)
                    
                    # 3. Database Insertion with Local Queue Fallback
                    try:
                        inserted, skipped = insert_observations(conn, observations, route_id, source_id)
                        window_result["rows_inserted"] = inserted
                        window_result["skipped_duplicates"] = skipped
                        if inserted == 0 and skipped > 0:
                            window_result["info"] = f"{skipped} flights already scraped today (database is up to date)"
                    except Exception as db_err:
                        logger.error(f"DATABASE_ERROR during insert for {window}: {db_err}")
                        logger.error(traceback.format_exc())
                        # Queue observations locally for retry
                        queue = _load_pending_queue()
                        queue.append({
                            "timestamp": datetime.now(self.timezone).isoformat(),
                            "route_id": route_id,
                            "source_id": source_id,
                            "window": window,
                            "observations": observations
                        })
                        _save_pending_queue(queue)
                        window_result["error"] = "DATABASE_ERROR_QUEUED"
                        window_result["info"] = f"Queued {len(observations)} observations locally due to DB failure."
                        results["status"] = "partial_failure"
                    
                except Exception as e:
                    logger.error(f"Unexpected error scraping {window}: {e}")
                    window_result["error"] = str(e)
                    results["status"] = "partial_failure"
                    
                results["details"].append(window_result)
                
        if all(w.get("error") for w in results["details"]):
            results["status"] = "failed"
            
        return results

scraping_service = ScrapingService()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing Scraping Service for T+1 and T+30...")
    res = scraping_service.run_scrape("DEL", "BOM", ["T+1", "T+30"])
    
    import json
    print(json.dumps(res, indent=2))
