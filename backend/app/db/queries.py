import logging
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

def get_or_create_source(conn, source_name: str, source_type: str) -> int:
    """
    Finds or creates a source and returns its ID.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT source_id FROM sources 
            WHERE source_name = %s
            """,
            (source_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
        logger.info(f"Creating new source: {source_name}")
        cursor.execute(
            """
            INSERT INTO sources (source_name, source_type)
            VALUES (%s, %s)
            RETURNING source_id
            """,
            (source_name, source_type)
        )
        source_id = cursor.fetchone()[0]
        conn.commit()
        return source_id

def get_or_create_route(conn, origin: str, destination: str, origin_city: str = "Unknown", destination_city: str = "Unknown") -> int:
    """
    Finds or creates a route based on origin and destination codes, returns its ID.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT route_id FROM routes 
            WHERE origin_airport = %s AND destination_airport = %s
            """,
            (origin, destination)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
        logger.info(f"Creating new route: {origin} -> {destination}")
        cursor.execute(
            """
            INSERT INTO routes (origin_airport, destination_airport, origin_city, destination_city)
            VALUES (%s, %s, %s, %s)
            RETURNING route_id
            """,
            (origin, destination, origin_city, destination_city)
        )
        route_id = cursor.fetchone()[0]
        conn.commit()
        return route_id

def insert_observations(conn, observations: list, route_id: int, source_id: int) -> int:
    """
    Inserts a list of parsed flight observations into the database.
    Skips duplicates based on unique constraint.
    """
    if not observations:
        return 0
        
    query = """
        INSERT INTO flight_observations (
            route_id, source_id, airline_name, flight_number,
            scrape_timestamp, departure_date, departure_time,
            advance_booking_window, cabin_class, fare_family,
            stops, seat_availability_hint, raw_price_displayed,
            base_fare, fuel_surcharge, taxes_fees, gst_amount,
            convenience_fee, currency, scrape_status,
            data_provenance, raw_payload_snapshot
        ) VALUES %s
        ON CONFLICT (route_id, source_id, flight_number, departure_date, scrape_timestamp)
        DO NOTHING
    """
    
    # Prepare data for execute_values
    values = []
    for obs in observations:
        values.append((
            route_id,
            source_id,
            obs["airline_name"],
            obs["flight_number"],
            obs["scrape_timestamp"],
            obs["departure_date"],
            obs["departure_time"],
            obs["advance_booking_window"],
            obs["cabin_class"],
            obs["fare_family"],
            obs["stops"],
            obs["seat_availability_hint"],
            obs["raw_price_displayed"],
            obs["base_fare"],
            obs["fuel_surcharge"],
            obs["taxes_fees"],
            obs["gst_amount"],
            obs["convenience_fee"],
            obs["currency"],
            obs["scrape_status"],
            obs["data_provenance"],
            obs["raw_payload_snapshot"]
        ))
        
    with conn.cursor() as cursor:
        # execute_values is much faster for bulk inserts
        execute_values(cursor, query, values)
        inserted_count = cursor.rowcount
        conn.commit()
        
    logger.info(f"Successfully inserted {inserted_count} new observations out of {len(observations)} total.")
    return inserted_count

if __name__ == "__main__":
    from app.db.connection import get_db_connection
    logging.basicConfig(level=logging.INFO)
    
    print("Testing database queries...")
    try:
        with get_db_connection() as conn:
            src_id = get_or_create_source(conn, "Google Flights SerpApi", "api")
            print(f"Source ID: {src_id}")
            
            rt_id = get_or_create_route(conn, "DEL", "BOM", "Delhi", "Mumbai")
            print(f"Route ID: {rt_id}")
            
            print("DB queries test successful.")
    except Exception as e:
        print(f"Test failed: {e}")
