import logging
from datetime import datetime, timedelta
import pytz

from app.scraper.serpapi_client import serpapi_client
from app.scraper.flight_parser import FlightParser
from app.db.connection import get_db_connection
from app.db.queries import get_or_create_source, get_or_create_route, insert_observations

logger = logging.getLogger(__name__)

class ScrapingService:
    def __init__(self):
        self.timezone = pytz.timezone("Asia/Kolkata")
        self.parser = FlightParser()
        # Default mapping of airport codes to cities for new routes
        # In a real app this would be a lookup table or another API call
        self.city_lookup = {
            "DEL": "Delhi",
            "BOM": "Mumbai"
        }

    def calculate_date_for_window(self, window: str) -> str:
        """
        Calculates the target departure date for a given booking window.
        """
        today = datetime.now(self.timezone)
        
        if window == "T+1":
            target = today + timedelta(days=1)
        elif window == "T+30":
            target = today + timedelta(days=30)
        else:
            raise ValueError(f"Unsupported booking window: {window}")
            
        return target.strftime("%Y-%m-%d")

    def run_scrape(self, origin: str, destination: str, windows: list) -> dict:
        """
        Coordinates the scraping process for a specific route and set of windows.
        """
        results = {
            "route": f"{origin}-{destination}",
            "windows": windows,
            "status": "success",
            "details": []
        }
        
        origin_city = self.city_lookup.get(origin, "Unknown")
        destination_city = self.city_lookup.get(destination, "Unknown")

        with get_db_connection() as conn:
            # Ensure Source and Route exist
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
                    
                    # 1. Fetch
                    api_response = serpapi_client.get_flights(origin, destination, target_date)
                    
                    if not api_response["success"]:
                        logger.error(f"API Error for {window}: {api_response['error']}")
                        window_result["error"] = api_response["error"]
                        results["status"] = "partial_failure"
                        results["details"].append(window_result)
                        continue
                        
                    # 2. Parse
                    observations = self.parser.parse_flights(api_response["data"], target_date, window)
                    window_result["flights_found"] = len(observations)
                    
                    # 3. Insert
                    inserted = insert_observations(conn, observations, route_id, source_id)
                    window_result["rows_inserted"] = inserted
                    
                except Exception as e:
                    logger.error(f"Unexpected error scraping {window}: {e}")
                    window_result["error"] = str(e)
                    results["status"] = "partial_failure"
                    
                results["details"].append(window_result)
                
        # If all windows failed, mark overall as failure
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
