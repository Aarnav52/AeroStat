import requests
import logging
from app.config import config

logger = logging.getLogger(__name__)

class SerpApiClient:
    def __init__(self):
        self.api_key = config.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search"

    def get_flights(self, origin: str, destination: str, date: str) -> dict:
        """
        Fetches flights using SerpApi Google Flights engine.
        
        :param origin: e.g. "DEL"
        :param destination: e.g. "BOM"
        :param date: e.g. "2026-09-15"
        """
        if not self.api_key:
            logger.error("SERPAPI_KEY is missing from configuration.")
            raise ValueError("SERPAPI_KEY not found.")
            
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": date,
            "type": "2",           # 2 = One-way flight
            "currency": "INR",     # Required for India pricing
            "hl": "en",
            "travel_class": "1",   # 1 = Economy
            "api_key": self.api_key
        }

        try:
            logger.info(f"Requesting flights from {origin} to {destination} for date {date} from SerpApi.")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.error(f"SerpApi returned an error: {data['error']}")
                return {"success": False, "error": data["error"]}
                
            return {"success": True, "data": data}

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request to SerpApi failed: {e}")
            return {"success": False, "error": str(e)}
        except ValueError as e: # Includes JSON decoding error
            logger.error(f"Failed to parse SerpApi response: {e}")
            return {"success": False, "error": "Invalid JSON response"}

# Provide a default instance
serpapi_client = SerpApiClient()

# Simple block to run/test standalone
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = SerpApiClient()
    # Test for DEL to BOM for T+1 (tomorrow)
    # Using a sample date based on current time
    print("Testing SerpApi Client...")
    result = client.get_flights("DEL", "BOM", "2026-09-15")
    if result["success"]:
        flights = result["data"].get("best_flights", []) + result["data"].get("other_flights", [])
        print(f"Found {len(flights)} total flights.")
    else:
        print(f"Failed: {result['error']}")
