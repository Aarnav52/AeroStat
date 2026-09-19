"""
Automation entrypoint: runs every scraper (SerpApi + the two compliant
direct-airline scrapers) across every active route in the DB, for
whichever booking windows are requested (default: all of T+1/7/15/30/45).

Not on a schedule yet (no cron/Airflow wired up) - this is the single
command that does a full sweep when run, the piece a scheduler would
call. Run: python -m app.scraper.run_all_scrapers
"""

import logging
import datetime

import pytz

from app.db.connection import get_db_connection
from app.db.queries import get_or_create_source, insert_observations
from app.services.scraping_service import scraping_service
from app.scraper.direct_scrapers import scrape_akasa, scrape_spicejet, ScrapeBlocked

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")
WINDOWS = {
    "T+1": 1,
    "T+7": 7,
    "T+15": 15,
    "T+30": 30,
    "T+45": 45,
}


def get_active_routes(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT route_id, origin_airport, destination_airport,
                   origin_city, destination_city
            FROM routes WHERE is_active = true ORDER BY route_id
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def direct_flight_to_observation(flight, route_id, window, departure_date, scrape_timestamp):
    return {
        "airline_name": flight["airline_name"],
        "flight_number": flight["flight_number"],
        "scrape_timestamp": scrape_timestamp,
        "departure_date": departure_date,
        "departure_time": flight["departure_time"],
        "advance_booking_window": window,
        "cabin_class": "economy",
        "fare_family": flight.get("fare_family"),
        "stops": 0 if (flight.get("stops_text") or "Non-stop") == "Non-stop" else 1,
        "seat_availability_hint": None,
        "raw_price_displayed": flight["raw_price_displayed"],
        "base_fare": None,
        "fuel_surcharge": None,
        "taxes_fees": None,
        "gst_amount": None,
        "convenience_fee": None,
        "currency": "INR",
        "scrape_status": "observed",
        "data_provenance": "real_scraped",
        "raw_payload_snapshot": __import__("json").dumps(flight),
    }


def _store_flights(conn, flights, source_name, route, window, target_date):
    if not flights:
        return 0
    source_id = get_or_create_source(conn, source_name, "airline_direct")
    # One timestamp for every observation in this scrape, matching the SerpApi path.
    scrape_timestamp = datetime.datetime.now(IST).isoformat()
    observations = [
        direct_flight_to_observation(f, route["route_id"], window, target_date, scrape_timestamp)
        for f in flights
    ]
    res = insert_observations(conn, observations, route["route_id"], source_id)
    return res[0] if isinstance(res, tuple) else res


def run_akasa(conn, route, window, target_date):
    try:
        flights = scrape_akasa(
            route["origin_airport"].strip(), route["origin_city"],
            route["destination_airport"].strip(), route["destination_city"],
            target_date,
        )
    except ScrapeBlocked as e:
        logger.info(f"Akasa blocked for route {route['route_id']} ({window}): {e}")
        return 0
    return _store_flights(conn, flights, "Akasa Air Direct", route, window, target_date)


def run_spicejet(conn, route, window, target_date):
    try:
        flights = scrape_spicejet(
            route["origin_airport"].strip(), route["destination_airport"].strip(), target_date,
        )
    except ScrapeBlocked as e:
        logger.info(f"SpiceJet blocked for route {route['route_id']} ({window}): {e}")
        return 0
    return _store_flights(conn, flights, "SpiceJet Direct", route, window, target_date)


def _run_pipeline_if_new_rows(inserted_count, label, summary):
    if inserted_count <= 0:
        logger.info(f"No new rows inserted in {label} phase - skipping pipeline run.")
        return
    try:
        from app.services.pipeline_service import pipeline_service
        logger.info(f"{label} phase inserted new rows - running cleaning + Jevons index pipeline...")
        pipeline_result = pipeline_service.run_full_pipeline()
        summary.setdefault("pipeline_runs", []).append({"phase": label, "result": pipeline_result})
        logger.info(f"Pipeline run ({label}): {pipeline_result}")
    except Exception as e:
        logger.error(f"Post-{label} pipeline run failed (index_values not updated this cycle): {e}")
        summary["errors"].append(f"pipeline/{label}: {e}")


def run_full_sweep(route_limit=None, windows=None):
    """
    windows: subset of WINDOWS keys to sweep (e.g. ["T+1"]). None/omitted
    means all of them - kept so a scheduler can run T+1 and T+30 on
    independent cadences (T+1 changes fast, T+30 barely moves day to day)
    without hitting SerpApi/the direct scrapers for windows nobody asked for.

    Two phases, run in that order: SerpApi (API call, seconds per route)
    across every route first, then the direct Playwright scrapers for
    Akasa/SpiceJet (much slower, and the source of the flaky retry loop)
    across every route. This way real SerpApi data lands and the index
    pipeline runs promptly instead of waiting behind the slow scrapers on
    route 1 before route 2's fast SerpApi call even starts.
    """
    active_windows = {w: WINDOWS[w] for w in windows} if windows else WINDOWS

    today = datetime.datetime.now(IST).date()
    summary = {"serpapi": 0, "akasa": 0, "spicejet": 0, "errors": []}

    with get_db_connection() as conn:
        routes = get_active_routes(conn)
        if route_limit is not None:
            routes = routes[:route_limit]

        # Phase 1: SerpApi across all routes - fast, so this pass alone
        # gets real data onto the charts before the slow scrapers even start.
        for route in routes:
            origin, dest = route["origin_airport"].strip(), route["destination_airport"].strip()
            logger.info(f"=== [SerpApi] Route {origin}-{dest} (route_id={route['route_id']}) ===")

            try:
                result = scraping_service.run_scrape(origin, dest, list(active_windows.keys()))
                inserted = sum(w.get("rows_inserted", 0) for w in result["details"])
                summary["serpapi"] += inserted
                logger.info(f"SerpApi: {inserted} rows inserted")
            except Exception as e:
                logger.error(f"SerpApi failed for {origin}-{dest}: {e}")
                summary["errors"].append(f"serpapi/{origin}-{dest}: {e}")

        _run_pipeline_if_new_rows(summary["serpapi"], "serpapi", summary)

        # Phase 2: direct Playwright scrapers (Akasa, SpiceJet) across all
        # routes - slow and flaky, trickles in after the fast pass above.
        for route in routes:
            origin, dest = route["origin_airport"].strip(), route["destination_airport"].strip()
            logger.info(f"=== [Direct] Route {origin}-{dest} (route_id={route['route_id']}) ===")

            for window, days_ahead in active_windows.items():
                target_date = (today + datetime.timedelta(days=days_ahead)).isoformat()

                try:
                    n = run_akasa(conn, route, window, target_date)
                    summary["akasa"] += n
                    logger.info(f"Akasa {window} ({target_date}): {n} rows inserted")
                except Exception as e:
                    logger.error(f"Akasa failed for {origin}-{dest} {window}: {e}")
                    summary["errors"].append(f"akasa/{origin}-{dest}/{window}: {e}")

                try:
                    n = run_spicejet(conn, route, window, target_date)
                    summary["spicejet"] += n
                    logger.info(f"SpiceJet {window} ({target_date}): {n} rows inserted")
                except Exception as e:
                    logger.error(f"SpiceJet failed for {origin}-{dest} {window}: {e}")
                    summary["errors"].append(f"spicejet/{origin}-{dest}/{window}: {e}")

        _run_pipeline_if_new_rows(summary["akasa"] + summary["spicejet"], "direct_scrapers", summary)

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sweep active routes for real fares.")
    parser.add_argument(
        "--window", action="append", choices=list(WINDOWS.keys()), dest="windows",
        help="Booking window to sweep (repeatable). Omit to sweep all windows.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only sweep the first N active routes (for testing).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = run_full_sweep(route_limit=args.limit, windows=args.windows)
    print("\n=== SWEEP SUMMARY ===")
    print(f"Windows:                 {args.windows or list(WINDOWS.keys())}")
    print(f"SerpApi rows inserted:   {result['serpapi']}")
    print(f"Akasa rows inserted:     {result['akasa']}")
    print(f"SpiceJet rows inserted:  {result['spicejet']}")
    if result.get("pipeline_runs"):
        print(f"Pipeline runs:           {[p['phase'] for p in result['pipeline_runs']]}")
    if result["errors"]:
        print(f"\n{len(result['errors'])} errors:")
        for e in result["errors"]:
            print(f"  - {e}")
