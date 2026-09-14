import json
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


class FlightParser:
    def __init__(self):
        self.timezone = pytz.timezone("Asia/Kolkata")

    def parse_flights(
        self,
        raw_data: dict,
        target_date: str,
        advance_window: str
    ) -> list:
        """
        Parses SerpApi Google Flights response into observation records.
        """

        observations = []

        # One timestamp for all observations from this scrape
        scrape_timestamp = datetime.now(self.timezone).isoformat()

        # SerpApi can return flights in both sections
        all_flights = (
            raw_data.get("best_flights", [])
            + raw_data.get("other_flights", [])
        )

        if not all_flights:
            logger.warning(
                f"No flights found in response for date {target_date}."
            )
            return []

        for flight in all_flights:
            try:
                # The 'flights' array contains the legs of the journey
                legs = flight.get("flights", [])

                if not legs:
                    logger.warning("Skipping flight with no flight legs.")
                    continue

                first_leg = legs[0]

                # -----------------------------------------
                # Airline name
                # -----------------------------------------
                airline_name = first_leg.get("airline", "Unknown")

                # -----------------------------------------
                # Flight number
                # -----------------------------------------
                # Combine airline + flight number for every leg.
                flight_numbers = [
                    f"{leg.get('airline', '')} "
                    f"{leg.get('flight_number', '')}".strip()
                    for leg in legs
                ]

                flight_number = (
                    ", ".join(flight_numbers)
                    if flight_numbers
                    else "Unknown"
                )

                # -----------------------------------------
                # Departure time
                # -----------------------------------------
                dep_time_str = (
                    first_leg
                    .get("departure_airport", {})
                    .get("time")
                )

                departure_date = target_date
                departure_time = None

                if dep_time_str:
                    try:
                        # Typical format:
                        # "2026-09-15 14:30"
                        dep_dt = datetime.strptime(
                            dep_time_str,
                            "%Y-%m-%d %H:%M"
                        )

                        departure_date = dep_dt.strftime("%Y-%m-%d")
                        departure_time = dep_dt.strftime("%H:%M:%S")

                    except ValueError:
                        logger.warning(
                            f"Could not parse departure time: "
                            f"{dep_time_str}"
                        )

                # -----------------------------------------
                # Stops
                # -----------------------------------------
                # Direct flight = 1 leg = 0 stops
                # One connection = 2 legs = 1 stop
                stops = len(legs) - 1

                # -----------------------------------------
                # Price
                # -----------------------------------------
                raw_price = flight.get("price")

                # If there is no price, the flight is unavailable/
                # sold out. We do NOT insert it because
                # raw_price_displayed is NOT NULL in the database.
                if raw_price is None:
                    logger.info(
                        f"Skipping flight with no price: "
                        f"{flight_number}"
                    )
                    continue

                scrape_status = "observed"

                # -----------------------------------------
                # Build observation
                # -----------------------------------------
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

                    # Price is guaranteed to be non-null here
                    "raw_price_displayed": raw_price,

                    # SerpApi currently does not reliably provide
                    # these individual fare components.
                    "base_fare": None,
                    "fuel_surcharge": None,
                    "taxes_fees": None,
                    "gst_amount": None,
                    "convenience_fee": None,

                    "currency": "INR",
                    "scrape_status": scrape_status,
                    "data_provenance": "real_scraped",

                    # Keep the original SerpApi flight object
                    # for auditing/debugging.
                    "raw_payload_snapshot": json.dumps(flight)
                }

                observations.append(observation)

            except Exception as e:
                # Do not create a database row here because
                # raw_price_displayed is NOT NULL.
                logger.error(
                    f"Error parsing flight record: {e}"
                )
                continue

        logger.info(
            f"Parsed {len(observations)} priced flight observations "
            f"for {target_date} ({advance_window})."
        )

        return observations


# ---------------------------------------------------------
# Standalone test
# ---------------------------------------------------------

if __name__ == "__main__":
    from app.scraper.serpapi_client import serpapi_client

    logging.basicConfig(level=logging.INFO)

    print("Fetching sample data for parser test...")

    # Get some real data to parse
    res = serpapi_client.get_flights(
        "DEL",
        "BOM",
        "2026-09-15"
    )

    if res["success"]:

        parser = FlightParser()

        obs = parser.parse_flights(
            res["data"],
            "2026-09-15",
            "T+1"
        )

        print(
            f"Successfully parsed "
            f"{len(obs)} observations."
        )

        if obs:
            print("Sample Observation:")

            sample = obs[0].copy()

            # Truncate snapshot for display
            sample["raw_payload_snapshot"] = (
                sample["raw_payload_snapshot"][:100]
                + "..."
            )

            print(
                json.dumps(
                    sample,
                    indent=2
                )
            )

    else:
        print("Failed to fetch data for test.")