"""
=============================================================================
Unit Tests for Batch 3 CPI Analyst Tools (agents/tools/quality_and_meta_tools.py)
=============================================================================
These tests verify the deterministic behavior of:
- get_data_quality_summary()
- get_supporting_observations()
- get_route_details()

All database calls are executed against controlled mock connections/cursors.
No live database or Supabase connection is required.
=============================================================================
"""

import unittest
from unittest.mock import MagicMock

from agents.tools.quality_and_meta_tools import (
    get_data_quality_summary,
    get_supporting_observations,
    get_route_details,
)


class TestBatch3Tools(unittest.TestCase):

    # -------------------------------------------------------------------------
    # 1. get_data_quality_summary() tests
    # -------------------------------------------------------------------------

    def test_get_data_quality_summary_normal_data(self):
        """get_data_quality_summary() computes factual metrics and breakdowns for a target date."""
        mock_cursor = MagicMock()
        # Side effects for sequential queries:
        # 1. MAX(observation_date) [not called if observation_date passed]
        # 2. Total obs
        # 3. Provenance breakdown
        # 4. Booking window breakdown
        # 5. Cabin class breakdown
        # 6. Unique routes & airlines
        # 7. Overall date range
        # 8. Quality flags
        mock_cursor.fetchone.side_effect = [
            (500,),          # total obs
            (5, 2),          # unique routes, unique airlines
            ("2026-01-01", "2026-02-01"), # min date, max date
        ]
        mock_cursor.fetchall.side_effect = [
            [("real_scraped", 400), ("synthetic", 100)], # provenance
            [("T+1", 200), ("T+7", 300)],                # booking window
            [("economy", 500)],                          # cabin class
            [("outlier_high", 2)],                       # quality flags
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_data_quality_summary(observation_date="2026-02-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["observation_date"], "2026-02-01")
        m = res["measured_metrics"]
        self.assertEqual(m["total_observations"], 500)
        self.assertEqual(m["unique_routes_count"], 5)
        self.assertEqual(m["unique_airlines_count"], 2)
        self.assertEqual(m["provenance_breakdown"], {"real_scraped": 400, "synthetic": 100})
        self.assertEqual(m["booking_window_breakdown"], {"T+1": 200, "T+7": 300})
        self.assertEqual(m["cabin_class_breakdown"], {"economy": 500})
        self.assertEqual(m["quality_flags_summary"], {"outlier_high": 2})
        self.assertEqual(m["overall_date_range"], {"min_date": "2026-01-01", "max_date": "2026-02-01"})

        # Ensure unsupported metrics are not fabricated
        self.assertIn("unavailable_metrics", res)
        self.assertIn("representativeness_score", res["unavailable_metrics"])

    def test_get_data_quality_summary_empty_database(self):
        """get_data_quality_summary() handles completely empty database cleanly."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,) # MAX(observation_date) is None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_data_quality_summary(conn=mock_conn)

        self.assertEqual(res["status"], "no_observations_found")
        self.assertIsNone(res["observation_date"])
        self.assertEqual(res["measured_metrics"]["total_observations"], 0)

    # -------------------------------------------------------------------------
    # 2. get_supporting_observations() tests
    # -------------------------------------------------------------------------

    def test_get_supporting_observations_filtered_and_limited(self):
        """get_supporting_observations() retrieves matching cleaned observations up to limit."""
        # Tuple format: observation_id, observation_date, route_id, flight_number, airline_code, cabin_class, advance_booking_window, clean_base_fare, data_provenance
        rows = [
            ("obs_101", "2026-02-01", "1", "AI-101", "AI", "economy", "T+1", 4500.0, "real_scraped"),
            ("obs_102", "2026-02-01", "1", "6E-202", "6E", "economy", "T+1", 4200.0, "real_scraped"),
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_supporting_observations(
            route_id="DEL-BOM",
            airline_code="AI",
            observation_date="2026-02-01",
            limit=10,
            conn=mock_conn,
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["count"], 2)
        self.assertEqual(len(res["observations"]), 2)
        self.assertEqual(res["query_filters"]["limit"], 10)

        obs1 = res["observations"][0]
        self.assertEqual(obs1["observation_id"], "obs_101")
        self.assertEqual(obs1["route_id"], "1")
        self.assertEqual(obs1["flight_number"], "AI-101")
        self.assertEqual(obs1["clean_base_fare"], 4500.0)

    def test_get_supporting_observations_invalid_limit_raises(self):
        """get_supporting_observations() raises ValueError for invalid limits."""
        with self.assertRaises(ValueError):
            get_supporting_observations(limit=0)

        with self.assertRaises(ValueError):
            get_supporting_observations(limit=1500)

    def test_get_supporting_observations_empty_result(self):
        """get_supporting_observations() returns empty list when no data matches."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_supporting_observations(airline_code="NONEXISTENT", conn=mock_conn)

        self.assertEqual(res["status"], "no_observations_found")
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["observations"], [])

    # -------------------------------------------------------------------------
    # 3. get_route_details() tests
    # -------------------------------------------------------------------------

    def test_get_route_details_existing_route(self):
        """get_route_details() returns route metadata for an existing route."""
        # Tuple format: route_id, origin_airport, destination_airport, origin_city, destination_city, dgca_monthly_passenger_volume, is_active, created_at
        row = ("1", "DEL", "BOM", "Delhi", "Mumbai", 450000, True, "2026-01-01T00:00:00")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_route_details("DEL-BOM", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["route_id"], "1")
        self.assertEqual(res["origin_airport"], "DEL")
        self.assertEqual(res["destination_airport"], "BOM")
        self.assertEqual(res["origin_city"], "Delhi")
        self.assertEqual(res["destination_city"], "Mumbai")
        self.assertEqual(res["dgca_monthly_passenger_volume"], 450000)
        self.assertTrue(res["is_active"])

    def test_get_route_details_missing_route(self):
        """get_route_details() handles missing route ID cleanly."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_route_details("9999", conn=mock_conn)

        self.assertEqual(res["status"], "route_not_found")
        self.assertEqual(res["route_id"], "9999")
        self.assertIn("not found", res["message"])

    def test_get_route_details_invalid_input_raises(self):
        """get_route_details() raises ValueError on empty or None route_id."""
        with self.assertRaises(ValueError):
            get_route_details("")

        with self.assertRaises(ValueError):
            get_route_details(None)


if __name__ == "__main__":
    unittest.main()
