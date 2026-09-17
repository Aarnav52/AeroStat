"""
=============================================================================
Unit Tests for Batch 2 CPI Analyst Tools (agents/tools/analysis_tools.py)
=============================================================================
These tests verify the deterministic behavior of:
- get_route_price_analysis()
- get_airline_price_analysis()
- get_booking_window_analysis()
- get_cabin_analysis()

All database calls are executed against controlled mock connections/cursors.
No live database or Supabase connection is required.
=============================================================================
"""

import unittest
from unittest.mock import MagicMock

from agents.tools.analysis_tools import (
    get_route_price_analysis,
    get_airline_price_analysis,
    get_booking_window_analysis,
    get_cabin_analysis,
)


class TestBatch2Tools(unittest.TestCase):

    # -------------------------------------------------------------------------
    # 1. get_route_price_analysis() tests
    # -------------------------------------------------------------------------

    def test_get_route_price_analysis_single_date(self):
        """get_route_price_analysis() returns route metrics for a single date."""
        # Tuple format: route_id, origin_airport, destination_airport, origin_city, destination_city, avg_fare, min_fare, max_fare, num_observations
        rows = [
            ("1", "DEL", "BOM", "Delhi", "Mumbai", 4500.0, 3500.0, 6000.0, 100),
            ("2", "DEL", "BLR", "Delhi", "Bengaluru", 5000.0, 4000.0, 7000.0, 80),
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_route_price_analysis("2026-02-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["observation_date"], "2026-02-01")
        self.assertIsNone(res["previous_date"])
        self.assertEqual(len(res["routes"]), 2)

        route1 = res["routes"][0]
        self.assertEqual(route1["route_id"], "1")
        self.assertEqual(route1["origin_airport"], "DEL")
        self.assertEqual(route1["destination_airport"], "BOM")
        self.assertEqual(route1["avg_fare"], 4500.0)
        self.assertEqual(route1["min_fare"], 3500.0)
        self.assertEqual(route1["max_fare"], 6000.0)
        self.assertEqual(route1["num_observations"], 100)

    def test_get_route_price_analysis_period_comparison(self):
        """get_route_price_analysis() compares route fares between two dates."""
        curr_rows = [
            ("1", "DEL", "BOM", "Delhi", "Mumbai", 4500.0, 3500.0, 6000.0, 100),
        ]
        prev_rows = [
            ("1", "DEL", "BOM", "Delhi", "Mumbai", 4000.0, 3200.0, 5500.0, 95),
        ]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [curr_rows, prev_rows]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_route_price_analysis("2026-02-01", previous_date="2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["routes"]), 1)
        r = res["routes"][0]
        self.assertEqual(r["avg_fare"], 4500.0)
        self.assertEqual(r["previous_avg_fare"], 4000.0)
        self.assertEqual(r["absolute_change"], 500.0)
        self.assertEqual(r["percentage_change"], 12.5)
        self.assertEqual(r["status"], "compared")

    def test_get_route_price_analysis_empty_results(self):
        """get_route_price_analysis() returns no_observations_found when date has no data."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_route_price_analysis("2026-05-01", conn=mock_conn)

        self.assertEqual(res["status"], "no_observations_found")
        self.assertEqual(res["routes"], [])

    # -------------------------------------------------------------------------
    # 2. get_airline_price_analysis() tests
    # -------------------------------------------------------------------------

    def test_get_airline_price_analysis_single_date(self):
        """get_airline_price_analysis() returns airline fare metrics and routes served count."""
        # Tuple format: airline_code, avg_fare, min_fare, max_fare, num_observations, routes_served_count
        rows = [
            ("6E", 4200.0, 3000.0, 6500.0, 300, 5),
            ("AI", 4800.0, 3500.0, 7500.0, 200, 4),
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_airline_price_analysis("2026-02-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["airlines"]), 2)
        indigo = res["airlines"][0]
        self.assertEqual(indigo["airline_code"], "6E")
        self.assertEqual(indigo["avg_fare"], 4200.0)
        self.assertEqual(indigo["routes_served_count"], 5)

    def test_get_airline_price_analysis_period_comparison(self):
        """get_airline_price_analysis() compares airline fares between two dates."""
        curr_rows = [("6E", 4200.0, 3000.0, 6500.0, 300, 5)]
        prev_rows = [("6E", 4000.0, 2900.0, 6000.0, 290, 5)]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [curr_rows, prev_rows]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_airline_price_analysis("2026-02-01", previous_date="2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["airlines"]), 1)
        air = res["airlines"][0]
        self.assertEqual(air["avg_fare"], 4200.0)
        self.assertEqual(air["previous_avg_fare"], 4000.0)
        self.assertEqual(air["absolute_change"], 200.0)
        self.assertEqual(air["percentage_change"], 5.0)

    # -------------------------------------------------------------------------
    # 3. get_booking_window_analysis() tests
    # -------------------------------------------------------------------------

    def test_get_booking_window_analysis_single_date(self):
        """get_booking_window_analysis() returns window metrics."""
        # Tuple format: advance_booking_window, avg_fare, min_fare, max_fare, num_observations
        rows = [
            ("T+1", 6500.0, 5000.0, 9000.0, 150),
            ("T+7", 4800.0, 3800.0, 6500.0, 180),
            ("T+30", 3800.0, 3000.0, 5000.0, 200),
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_booking_window_analysis("2026-02-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["booking_windows"]), 3)
        w1 = res["booking_windows"][0]
        self.assertEqual(w1["advance_booking_window"], "T+1")
        self.assertEqual(w1["avg_fare"], 6500.0)

    def test_get_booking_window_analysis_period_comparison(self):
        """get_booking_window_analysis() compares window fares between two dates."""
        curr_rows = [("T+1", 6500.0, 5000.0, 9000.0, 150)]
        prev_rows = [("T+1", 6000.0, 4800.0, 8500.0, 140)]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [curr_rows, prev_rows]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_booking_window_analysis("2026-02-01", previous_date="2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        win = res["booking_windows"][0]
        self.assertEqual(win["absolute_change"], 500.0)
        self.assertEqual(round(win["percentage_change"], 2), 8.33)

    # -------------------------------------------------------------------------
    # 4. get_cabin_analysis() tests
    # -------------------------------------------------------------------------

    def test_get_cabin_analysis_single_date(self):
        """get_cabin_analysis() returns cabin class fare metrics."""
        # Tuple format: cabin_class, avg_fare, min_fare, max_fare, num_observations
        rows = [
            ("economy", 4200.0, 3000.0, 7000.0, 400),
            ("business", 18000.0, 14000.0, 25000.0, 50),
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_cabin_analysis("2026-02-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["cabins"]), 2)
        eco = res["cabins"][0]
        self.assertEqual(eco["cabin_class"], "economy")
        self.assertEqual(eco["avg_fare"], 4200.0)

    def test_get_cabin_analysis_period_comparison(self):
        """get_cabin_analysis() compares cabin fares between two dates."""
        curr_rows = [("economy", 4200.0, 3000.0, 7000.0, 400)]
        prev_rows = [("economy", 4000.0, 2900.0, 6800.0, 390)]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [curr_rows, prev_rows]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_cabin_analysis("2026-02-01", previous_date="2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        cab = res["cabins"][0]
        self.assertEqual(cab["avg_fare"], 4200.0)
        self.assertEqual(cab["previous_avg_fare"], 4000.0)
        self.assertEqual(cab["absolute_change"], 200.0)
        self.assertEqual(cab["percentage_change"], 5.0)


if __name__ == "__main__":
    unittest.main()
