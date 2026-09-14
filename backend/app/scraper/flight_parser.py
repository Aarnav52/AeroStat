import json
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class FlightParser:
    def __init__(self):
        self.timezone = pytz.timezone("Asia/Kolkata")

    def parse_flights(self, raw_data: dict, target_date: str, advance_window: str) -> list:
        """
        Parses SerpApi Google Flights response into observation records.
        """
        observations = []
        scrape_timestamp = datetime.now(self.timezone).isoformat()
        
        all_flights = raw_data.get("best_flights", []) + raw_data.get("other_flights", [])
        
        if not all_flights:
            logger.warning(f"No flights found in response for date {target_date}.")
            # Return a 'sold_out' or empty observation if required, but usually we just skip.
            # Let's return a special record to denote no flights found if we want to track it,
            # or just return an empty list. The requirements say:
            # "For unavailable flights: scrape_status = 'sold_out'"
            # But normally we don't have a flight number for sold out. 
            # We'll just return an empty list here, and handle 'sold_out' at the service level 
            # if the list is empty.
            return []

        for flight in all_flights:
            try:
                # The 'flights' array contains the legs of the journey
                legs = flight.get("flights", [])
                if not legs:
                    continue
                
                first_leg = legs[0]
                
                # Airline name
                airline_name = first_leg.get("airline", "Unknown")
                
                # Flight number: combine all legs or just use the first one. 
                # For simplicity, we use the first leg's flight number or combine them.
                flight_numbers = [f"{leg.get('airline', '')} {leg.get('flight_number', '')}".strip() for leg in legs]
                flight_number = ", ".join(flight_numbers) if flight_numbers else "Unknown"

                # Departure time parsing
                dep_time_str = first_leg.get("departure_airport", {}).get("time")
                departure_date = target_date
                departure_time = None
                
                if dep_time_str:
                    # typical format: "2026-09-15 14:30"
                    try:
                        dep_dt = datetime.strptime(dep_time_str, "%Y-%m-%d %H:%M")
                        departure_date = dep_dt.strftime("%Y-%m-%d")
                        departure_time = dep_dt.strftime("%H:%M:%S")
                    except ValueError:
                        logger.warning(f"Could not parse departure time: {dep_time_str}")

                # Stops
                # Sometimes layovers array exists, or we just do len(legs) - 1
                stops = len(legs) - 1

                # Price
                raw_price = flight.get("price")
                if raw_price is None:
                    # If price is missing, it might be sold out or unavailable
                    scrape_status = 'sold_out'
                else:
                    scrape_status = 'observed'

                observation = {
                    "airline_name": airline_name,
                    "flight_number": flight_number,
                    "scrape_timestamp": scrape_timestamp,
                    "departure_date": departure_date,
                    "departure_time": departure_time,
                    "advance_booking_window": advance_window,
                    "cabin_class": "economy",
                    "fare_family": None,
                    "stops": stops,
                    "seat_availability_hint": None,
                    "raw_price_displayed": raw_price,
                    "base_fare": None,
                    "fuel_surcharge": None,
                    "taxes_fees": None,
                    "gst_amount": None,
                    "convenience_fee": None,
                    "currency": "INR",
                    "scrape_status": scrape_status,
                    "data_provenance": "real_scraped",
                    "raw_payload_snapshot": json.dumps(flight)
                }
                
                observations.append(observation)
                
            except Exception as e:
                logger.error(f"Error parsing flight record: {e}")
                # Add a parse error record
                observations.append({
                    "airline_name": "Unknown",
                    "flight_number": "Unknown",
                    "scrape_timestamp": scrape_timestamp,
                    "departure_date": target_date,
                    "departure_time": None,
                    "advance_booking_window": advance_window,
                    "cabin_class": "economy",
                    "fare_family": None,
                    "stops": 0,
                    "seat_availability_hint": None,
                    "raw_price_displayed": None,
                    "base_fare": None,
                    "fuel_surcharge": None,
                    "taxes_fees": None,
                    "gst_amount": None,
                    "convenience_fee": None,
                    "currency": "INR",
                    "scrape_status": "parse_error",
                    "data_provenance": "real_scraped",
                    "raw_payload_snapshot": json.dumps(flight) if flight else "{}"
                })

        return observations

# Standalone test
if __name__ == "__main__":
    from app.scraper.serpapi_client import serpapi_client
    logging.basicConfig(level=logging.INFO)
    
    print("Fetching sample data for parser test...")
    # Get some real data to parse
    res = serpapi_client.get_flights("DEL", "BOM", "2026-09-15")
    if res["success"]:
        parser = FlightParser()
        obs = parser.parse_flights(res["data"], "2026-09-15", "T+1")
        print(f"Successfully parsed {len(obs)} observations.")
        if obs:
            print("Sample Observation:")
            sample = obs[0].copy()
            # Truncate snapshot for display
            sample["raw_payload_snapshot"] = sample["raw_payload_snapshot"][:100] + "..."
            print(json.dumps(sample, indent=2))
    else:
        print("Failed to fetch data for test.")
