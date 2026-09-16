import logging
from psycopg2.extras import execute_values

from app.services.fee_decomposition import decompose_fare, load_schedule

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

def _apply_fee_decomposition(conn, observations: list, route_id: int) -> None:
    """
    Fills base_fare/fuel_surcharge/taxes_fees/gst_amount/udf/fee_derivation
    in place for any observation that's missing them and whose airline has a
    tariff-sheet schedule for this route's origin station. Never fabricates:
    observations for airlines/stations with no schedule are left untouched
    (base_fare stays NULL, fee_derivation stays unset).
    """
    needs_decomp = [obs for obs in observations if obs.get("base_fare") is None]
    if not needs_decomp:
        return

    with conn.cursor() as cursor:
        cursor.execute("SELECT origin_airport FROM routes WHERE route_id = %s", (route_id,))
        row = cursor.fetchone()
    if not row:
        return
    origin_station = row[0].strip()

    schedule_cache = {}
    for obs in needs_decomp:
        airline_name = obs["airline_name"]
        if airline_name not in schedule_cache:
            schedule_cache[airline_name] = load_schedule(conn, airline_name, origin_station)
        schedule_rows = schedule_cache[airline_name]
        if not schedule_rows:
            continue

        decomposed = decompose_fare(schedule_rows, obs["raw_price_displayed"])
        if decomposed is None:
            continue

        obs["base_fare"] = decomposed["base_fare"]
        obs["fuel_surcharge"] = decomposed["fuel_surcharge"]
        obs["taxes_fees"] = decomposed["taxes_fees"]
        obs["gst_amount"] = decomposed["gst_amount"]
        obs["udf"] = decomposed["udf"]
        obs["fee_derivation"] = decomposed["fee_derivation"]


def insert_observations(conn, observations: list, route_id: int, source_id: int) -> int:
    """
    Inserts a list of parsed flight observations into the database.
    Skips duplicates based on unique constraint.

    The DB's unique constraint includes scrape_timestamp, which is set to
    "now" per scrape call. Skip any observation whose exact flight, departure
    date, booking window, and price was already scraped within the last 15 minutes
    for this route/source. This prevents rapid re-run duplication while allowing
    subsequent live scrapes and price updates to be recorded.
    """
    if not observations:
        return 0, 0

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT flight_number, to_char(departure_date, 'YYYY-MM-DD'), advance_booking_window, raw_price_displayed
            FROM flight_observations
            WHERE route_id = %s AND source_id = %s
              AND scrape_timestamp >= (now() - INTERVAL '15 minutes')
            """,
            (route_id, source_id)
        )
        recently_scraped = set(cursor.fetchall())

    deduped = [
        obs for obs in observations
        if (obs["flight_number"], str(obs["departure_date"]), obs["advance_booking_window"], obs.get("raw_price_displayed"))
        not in recently_scraped
    ]
    skipped_recent = len(observations) - len(deduped)
    if skipped_recent:
        logger.info(
            f"Skipping {skipped_recent} observation(s) scraped within last 15 minutes with identical price "
            f"for route_id={route_id} source_id={source_id}."
        )
    observations = deduped
    if not observations:
        return 0, skipped_same_day

    _apply_fee_decomposition(conn, observations, route_id)

    query = """
        INSERT INTO flight_observations (
            route_id, source_id, airline_name, flight_number,
            scrape_timestamp, departure_date, departure_time,
            advance_booking_window, cabin_class, fare_family,
            stops, seat_availability_hint, raw_price_displayed,
            base_fare, fuel_surcharge, taxes_fees, gst_amount, udf,
            convenience_fee, currency, scrape_status,
            data_provenance, raw_payload_snapshot, fee_derivation
        ) VALUES %s
        ON CONFLICT (route_id, source_id, flight_number, departure_date, scrape_timestamp)
        DO NOTHING
        RETURNING observation_id
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
            obs.get("udf"),
            obs["convenience_fee"],
            obs["currency"],
            obs["scrape_status"],
            obs["data_provenance"],
            obs["raw_payload_snapshot"],
            obs.get("fee_derivation"),
        ))
        
    with conn.cursor() as cursor:
        inserted_rows = execute_values(cursor, query, values, fetch=True)
        inserted_count = len(inserted_rows) if inserted_rows else 0
        conn.commit()
        
    logger.info(f"Successfully inserted {inserted_count} new observations out of {len(observations)} total (skipped {skipped_same_day} duplicate/already scraped).")
    return inserted_count, skipped_same_day

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
