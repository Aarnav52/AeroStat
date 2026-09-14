import logging
from app.db.connection import get_db_connection
from app.db.queries import get_or_create_source, get_or_create_route, insert_observations
from app.scraper.serpapi_client import serpapi_client
from app.scraper.flight_parser import FlightParser

logging.basicConfig(level=logging.INFO)

def test():
    print("Fetching flights...")
    res = serpapi_client.get_flights("DEL", "BOM", "2026-09-15")
    if not res["success"]:
        print("Failed to fetch")
        return
        
    print("Parsing flights...")
    parser = FlightParser()
    observations = parser.parse_flights(res["data"], "2026-09-15", "T+1")
    
    print(f"Inserting {len(observations)} flights...")
    with get_db_connection() as conn:
        src_id = get_or_create_source(conn, "Google Flights SerpApi", "api")
        rt_id = get_or_create_route(conn, "DEL", "BOM", "Delhi", "Mumbai")
        
        inserted = insert_observations(conn, observations, rt_id, src_id)
        print(f"Inserted {inserted} rows!")

if __name__ == "__main__":
    test()
