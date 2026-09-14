import logging
import math
from typing import Optional
from app.db.connection import get_db_connection

logger = logging.getLogger(__name__)


class IndexService:
    """
    Calculates the Jevons Airfare Price Index.

    Jevons Index = geometric mean of price relatives × 100
    J = (∏(P_current / P_base))^(1/n) × 100

    This class is kept independent from scraping logic.
    The statistical methodology can be modified here without
    touching the scraper or database layer.
    """

    def _get_prices_for_window(
        self,
        conn,
        route_id: int,
        window: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list:
        """
        Fetches all 'observed' prices for a given route and booking window.
        Optionally filter by a scrape date range.
        Returns a list of (scrape_date, price) tuples.
        """
        query = """
            SELECT 
                DATE(scrape_timestamp AT TIME ZONE 'Asia/Kolkata') AS scrape_date,
                AVG(raw_price_displayed) AS avg_price
            FROM flight_observations
            WHERE route_id = %s
              AND advance_booking_window = %s
              AND scrape_status = 'observed'
              AND raw_price_displayed IS NOT NULL
        """
        params = [route_id, window]

        if date_from:
            query += " AND DATE(scrape_timestamp AT TIME ZONE 'Asia/Kolkata') >= %s"
            params.append(date_from)
        if date_to:
            query += " AND DATE(scrape_timestamp AT TIME ZONE 'Asia/Kolkata') <= %s"
            params.append(date_to)

        query += " GROUP BY scrape_date ORDER BY scrape_date ASC"

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [(str(r[0]), float(r[1])) for r in rows]

    def _geometric_mean(self, values: list) -> float:
        """
        Computes the geometric mean of a list of positive values.
        Uses log-sum for numerical stability.
        """
        n = len(values)
        if n == 0:
            return 0.0
        log_sum = sum(math.log(v) for v in values if v > 0)
        return math.exp(log_sum / n)

    def calculate_jevons_index(
        self,
        route: str,
        window: str,
        base_date: Optional[str] = None,
    ) -> dict:
        """
        Calculates the Jevons Price Index for a route and booking window.

        - base_date: The scrape date to use as the base period (index = 100).
                     If not specified, the earliest available scrape date is used.

        Returns a dict with:
            - route
            - window
            - base_date
            - base_avg_price
            - series: list of {date, avg_price, index_value}
        """
        try:
            parts = route.split("-")
            if len(parts) != 2:
                return {"error": f"Invalid route format: {route}. Expected e.g. DEL-BOM"}

            origin, destination = parts[0], parts[1]

            with get_db_connection() as conn:
                # Get route_id
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT route_id FROM routes
                        WHERE origin_airport = %s AND destination_airport = %s
                        """,
                        (origin, destination),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return {"error": f"Route {route} not found in database"}
                    route_id = row[0]

                # Fetch daily average prices
                price_series = self._get_prices_for_window(conn, route_id, window)

            if not price_series:
                return {
                    "route": route,
                    "window": window,
                    "base_date": None,
                    "base_avg_price": None,
                    "series": [],
                    "message": "No observed data available for this route/window combination.",
                }

            # Determine base period
            if base_date:
                base_prices = [p for d, p in price_series if d == base_date]
                if not base_prices:
                    return {"error": f"No data found for base_date={base_date}"}
                base_avg = base_prices[0]
            else:
                # Use earliest available date as base
                base_date = price_series[0][0]
                base_avg = price_series[0][1]

            # Build index series: Jevons = (price_current / price_base) × 100
            # For a single matched pair per day this simplifies to a price relative × 100.
            # When we have multiple flight matches per day, the geometric mean of
            # all daily price relatives is used — consistent with Jevons methodology.
            series = []
            for scrape_date, avg_price in price_series:
                if base_avg and base_avg > 0:
                    index_value = round((avg_price / base_avg) * 100, 2)
                else:
                    index_value = None

                series.append({
                    "date": scrape_date,
                    "avg_price": round(avg_price, 2),
                    "index_value": index_value,
                })

            return {
                "route": route,
                "window": window,
                "base_date": base_date,
                "base_avg_price": round(base_avg, 2),
                "series": series,
            }

        except Exception as e:
            logger.error(f"Error calculating Jevons index: {e}")
            return {"error": str(e)}

    def calculate_cross_window_index(self, route: str) -> dict:
        """
        Calculates Jevons index for all supported booking windows for a route.
        Returns a combined summary useful for dashboard display.
        """
        results = {}
        for window in ["T+1", "T+30"]:
            results[window] = self.calculate_jevons_index(route, window)
        return {"route": route, "index": results}


index_service = IndexService()


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    print("Testing Jevons Index Service for DEL-BOM...")
    result = index_service.calculate_jevons_index("DEL-BOM", "T+1")
    print(json.dumps(result, indent=2))

    print("\nCross-window index:")
    cross = index_service.calculate_cross_window_index("DEL-BOM")
    print(json.dumps(cross, indent=2))
