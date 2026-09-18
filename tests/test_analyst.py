"""
=============================================================================
Unit Tests for Analyst API Router (backend/app/api/analyst.py)
=============================================================================
These tests verify that:
1. GET /analyst/tools returns all 10 tool schemas.
2. POST /analyst/tools/execute dispatches tools and handles errors cleanly.
3. Direct analyst endpoints return valid JSON-serializable responses.
4. Unknown tools return HTTP 404.
5. Invalid parameters return HTTP 400.
=============================================================================
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend package path is in sys.path
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAnalystAPI(unittest.TestCase):

    def test_list_analyst_tools_endpoint(self):
        """GET /analyst/tools returns schemas for all 10 analyst tools."""
        response = client.get("/analyst/tools")
        self.assertEqual(response.status_code, 200)
        schemas = response.json()
        self.assertEqual(len(schemas), 10)
        names = {s["name"] for s in schemas}
        self.assertIn("get_latest_cpi", names)
        self.assertIn("get_route_details", names)

    @patch("agents.tools.cpi_tools.get_db_connection")
    def test_execute_tool_success(self, mock_get_db):
        """POST /analyst/tools/execute executes valid tool calls."""
        row = (1, "2026-02-01", "2026-01-01", "national", None, None, 105.0, 500, None, "2026-02-01T10:00:00")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn

        payload = {
            "tool_name": "get_latest_cpi",
            "arguments": {"index_type": "national"}
        }
        response = client.post("/analyst/tools/execute", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["index_type"], "national")
        self.assertEqual(data["index_value"], 105.0)

    def test_execute_unknown_tool_returns_404(self):
        """POST /analyst/tools/execute returns 404 for unknown tools."""
        payload = {"tool_name": "non_existent_tool", "arguments": {}}
        response = client.post("/analyst/tools/execute", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Unknown tool", response.json()["detail"])

    def test_execute_invalid_arguments_returns_400(self):
        """POST /analyst/tools/execute returns 400 for invalid keyword parameters."""
        payload = {"tool_name": "get_latest_cpi", "arguments": {"invalid_arg": "val"}}
        response = client.post("/analyst/tools/execute", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid arguments", response.json()["detail"])

    @patch("agents.tools.cpi_tools.get_db_connection")
    def test_cpi_latest_endpoint(self, mock_get_db):
        """GET /analyst/cpi/latest returns latest CPI observation."""
        row = (1, "2026-02-01", "2026-01-01", "national", None, None, 105.0, 500, None, "2026-02-01T10:00:00")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn

        response = client.get("/analyst/cpi/latest?index_type=national")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["index_value"], 105.0)

    @patch("agents.tools.cpi_tools.get_db_connection")
    def test_cpi_history_endpoint(self, mock_get_db):
        """GET /analyst/cpi/history returns chronological history."""
        rows = [
            (1, "2026-01-01", "2026-01-01", "national", None, None, 100.0, 500, None, "2026-01-01T10:00:00"),
            (2, "2026-02-01", "2026-01-01", "national", None, None, 105.0, 500, None, "2026-02-01T10:00:00"),
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn

        response = client.get("/analyst/cpi/history?start_date=2026-01-01&end_date=2026-02-01")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["index_value"], 100.0)

    @patch("agents.tools.cpi_tools.get_db_connection")
    def test_cpi_compare_endpoint(self, mock_get_db):
        """POST /analyst/cpi/compare compares two dates."""
        curr_row = (2, "2026-02-01", "2026-01-01", "national", None, None, 110.0, 500, None, "2026-02-01T10:00:00")
        prev_row = (1, "2026-01-01", "2026-01-01", "national", None, None, 100.0, 500, None, "2026-01-01T10:00:00")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [curr_row, prev_row]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn

        payload = {"current_date": "2026-02-01", "previous_date": "2026-01-01"}
        response = client.post("/analyst/cpi/compare", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["absolute_change"], 10.0)

    @patch("agents.tools.cpi_tools.get_db_connection")
    def test_route_details_endpoint(self, mock_get_db):
        """GET /analyst/routes/{route_id} returns route details."""
        row = (1, "DEL", "BOM", "Delhi", "Mumbai", 450000, True, "2026-01-01T00:00:00")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn

        response = client.get("/analyst/routes/DEL-BOM")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["origin_airport"], "DEL")

    @patch("agents.tools.cpi_tools.get_db_connection")
    def test_route_details_not_found(self, mock_get_db):
        """GET /analyst/routes/{route_id} returns 404 if route not found."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn

        response = client.get("/analyst/routes/9999")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
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
"""
=============================================================================
Unit Tests for Batch 1 CPI Analyst Tools (agents/tools/cpi_tools.py)
=============================================================================
These tests verify the deterministic behavior of:
- get_latest_cpi()
- get_cpi_history()
- compare_cpi_periods()

All database calls are executed against controlled mock connections/cursors.
No live database or Supabase connection is required.
=============================================================================
"""

import unittest
from unittest.mock import MagicMock
from datetime import date, datetime

from agents.tools.cpi_tools import (
    get_latest_cpi,
    get_cpi_history,
    compare_cpi_periods,
)


class TestCpiTools(unittest.TestCase):

    def _sample_row(
        self,
        row_id=1,
        obs_date="2026-02-01",
        base_date="2026-01-01",
        index_type="national",
        route_id=None,
        booking_window=None,
        index_val=105.0,
        obs_count=500,
        provenance=None,
        calc_at="2026-02-01T10:00:00",
    ):
        return (
            row_id,
            obs_date,
            base_date,
            index_type,
            route_id,
            booking_window,
            index_val,
            obs_count,
            provenance or {"real_scraped": obs_count},
            calc_at,
        )

    # -------------------------------------------------------------------------
    # 1. get_latest_cpi() tests
    # -------------------------------------------------------------------------

    def test_get_latest_cpi_returns_latest_observation(self):
        """get_latest_cpi() returns the latest observation record with all expected schema fields."""
        row = self._sample_row(row_id=42, obs_date="2026-02-15", index_val=108.25)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_latest_cpi(index_type="national", conn=mock_conn)

        self.assertIsNotNone(res)
        self.assertEqual(res["id"], 42)
        self.assertEqual(res["observation_date"], "2026-02-15")
        self.assertEqual(res["base_period_date"], "2026-01-01")
        self.assertEqual(res["index_type"], "national")
        self.assertIsNone(res["route_id"])
        self.assertIsNone(res["advance_booking_window"])
        self.assertEqual(res["index_value"], 108.25)
        self.assertEqual(res["num_observations_used"], 500)
        self.assertEqual(res["data_provenance_mix"], {"real_scraped": 500})
        self.assertEqual(res["calculated_at"], "2026-02-01T10:00:00")

        # Verify SQL query executed
        executed_sql = mock_cursor.execute.call_args[0][0]
        params = mock_cursor.execute.call_args[0][1]
        self.assertIn("ORDER BY observation_date DESC", executed_sql)
        self.assertIn("LIMIT 1", executed_sql)
        self.assertEqual(params, ("national",))

    def test_get_latest_cpi_handles_no_available_data(self):
        """get_latest_cpi() returns None when index_values is empty or no records match."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_latest_cpi(index_type="route", route_id="DEL-BOM", conn=mock_conn)

        self.assertIsNone(res)

    # -------------------------------------------------------------------------
    # 2. get_cpi_history() tests
    # -------------------------------------------------------------------------

    def test_get_cpi_history_returns_chronological_records(self):
        """get_cpi_history() returns records ordered chronologically and respects date filters."""
        rows = [
            self._sample_row(row_id=1, obs_date="2026-01-01", index_val=100.0),
            self._sample_row(row_id=2, obs_date="2026-01-08", index_val=102.5),
            self._sample_row(row_id=3, obs_date="2026-01-15", index_val=105.0),
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_cpi_history("2026-01-01", "2026-01-15", index_type="national", conn=mock_conn)

        self.assertEqual(len(res), 3)
        self.assertEqual(res[0]["observation_date"], "2026-01-01")
        self.assertEqual(res[1]["observation_date"], "2026-01-08")
        self.assertEqual(res[2]["observation_date"], "2026-01-15")
        self.assertEqual(res[0]["index_value"], 100.0)
        self.assertEqual(res[1]["index_value"], 102.5)
        self.assertEqual(res[2]["index_value"], 105.0)

        executed_sql = mock_cursor.execute.call_args[0][0]
        self.assertIn("ORDER BY observation_date ASC", executed_sql)

    def test_get_cpi_history_returns_empty_when_no_match(self):
        """get_cpi_history() returns empty list [] when no observations exist in date range."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = get_cpi_history("2026-05-01", "2026-05-31", conn=mock_conn)

        self.assertEqual(res, [])

    def test_get_cpi_history_invalid_date_format_raises(self):
        """get_cpi_history() raises ValueError on malformed date string."""
        with self.assertRaises(ValueError):
            get_cpi_history("invalid-date", "2026-01-15")

    def test_get_cpi_history_reversed_date_range_raises(self):
        """get_cpi_history() raises ValueError when start_date is after end_date."""
        with self.assertRaises(ValueError):
            get_cpi_history("2026-02-01", "2026-01-01")

    # -------------------------------------------------------------------------
    # 3. compare_cpi_periods() tests
    # -------------------------------------------------------------------------

    def test_compare_cpi_periods_positive_and_negative_change(self):
        """compare_cpi_periods() correctly calculates positive and negative absolute/percentage changes."""
        curr_row = self._sample_row(row_id=2, obs_date="2026-02-01", index_val=110.0)
        prev_row = self._sample_row(row_id=1, obs_date="2026-01-01", index_val=100.0)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [curr_row, prev_row]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = compare_cpi_periods("2026-02-01", "2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["current_value"], 110.0)
        self.assertEqual(res["previous_value"], 100.0)
        self.assertEqual(res["absolute_change"], 10.0)
        self.assertEqual(res["percentage_change"], 10.0)
        self.assertEqual(res["percentage_change_status"], "ok")

        # Test negative change
        curr_row_neg = self._sample_row(row_id=4, obs_date="2026-03-01", index_val=95.0)
        prev_row_neg = self._sample_row(row_id=3, obs_date="2026-02-01", index_val=100.0)

        mock_cursor_neg = MagicMock()
        mock_cursor_neg.fetchone.side_effect = [curr_row_neg, prev_row_neg]
        mock_conn_neg = MagicMock()
        mock_conn_neg.cursor.return_value.__enter__.return_value = mock_cursor_neg

        res_neg = compare_cpi_periods("2026-03-01", "2026-02-01", conn=mock_conn_neg)

        self.assertEqual(res_neg["absolute_change"], -5.0)
        self.assertEqual(res_neg["percentage_change"], -5.0)

    def test_compare_cpi_periods_handles_zero_previous_value(self):
        """compare_cpi_periods() handles previous_value == 0 without zero-division errors."""
        curr_row = self._sample_row(row_id=2, obs_date="2026-02-01", index_val=105.0)
        prev_row = self._sample_row(row_id=1, obs_date="2026-01-01", index_val=0.0)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [curr_row, prev_row]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = compare_cpi_periods("2026-02-01", "2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["absolute_change"], 105.0)
        self.assertIsNone(res["percentage_change"])
        self.assertEqual(res["percentage_change_status"], "undefined_division_by_zero")

    def test_compare_cpi_periods_handles_missing_current_observation(self):
        """compare_cpi_periods() handles missing current observation cleanly."""
        prev_row = self._sample_row(row_id=1, obs_date="2026-01-01", index_val=100.0)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, prev_row]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = compare_cpi_periods("2026-02-01", "2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "missing_current_observation")
        self.assertIsNone(res["current_value"])
        self.assertEqual(res["previous_value"], 100.0)
        self.assertIsNone(res["absolute_change"])
        self.assertIsNone(res["percentage_change"])

    def test_compare_cpi_periods_handles_missing_previous_observation(self):
        """compare_cpi_periods() handles missing previous observation cleanly."""
        curr_row = self._sample_row(row_id=2, obs_date="2026-02-01", index_val=105.0)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [curr_row, None]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = compare_cpi_periods("2026-02-01", "2026-01-01", conn=mock_conn)

        self.assertEqual(res["status"], "missing_previous_observation")
        self.assertEqual(res["current_value"], 105.0)
        self.assertIsNone(res["previous_value"])
        self.assertIsNone(res["absolute_change"])
        self.assertIsNone(res["percentage_change"])

    def test_compare_cpi_periods_handles_same_date(self):
        """compare_cpi_periods() handles current_date == previous_date explicitly."""
        curr_row = self._sample_row(row_id=1, obs_date="2026-02-01", index_val=105.0)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [curr_row, curr_row]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        res = compare_cpi_periods("2026-02-01", "2026-02-01", conn=mock_conn)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["absolute_change"], 0.0)
        self.assertEqual(res["percentage_change"], 0.0)
        self.assertEqual(res["percentage_change_status"], "same_date")


if __name__ == "__main__":
    unittest.main()
"""
=============================================================================
Unit Tests for Tool Registry & Dispatcher (agents/tools/registry.py)
=============================================================================
These tests verify that:
1. All 10 deterministic tools are registered.
2. Tool names are unique.
3. Parameter schemas contain expected parameter names and required fields.
4. Dispatcher routes execution to the correct tool function.
5. Unknown tool names produce clear structured error outputs.
6. Execution results are JSON-serializable.
=============================================================================
"""

import json
import unittest
from unittest.mock import MagicMock

from agents.tools.registry import (
    TOOL_REGISTRY,
    get_tool_registry,
    get_tool_schemas,
    dispatch_tool,
)


class TestToolRegistry(unittest.TestCase):

    EXPECTED_10_TOOLS = {
        "get_latest_cpi",
        "get_cpi_history",
        "compare_cpi_periods",
        "get_route_price_analysis",
        "get_airline_price_analysis",
        "get_booking_window_analysis",
        "get_cabin_analysis",
        "get_data_quality_summary",
        "get_supporting_observations",
        "get_route_details",
    }

    def test_all_10_tools_are_registered(self):
        """All 10 deterministic tools must be present in TOOL_REGISTRY."""
        registry = get_tool_registry()
        self.assertEqual(len(registry), 10)
        self.assertEqual(set(registry.keys()), self.EXPECTED_10_TOOLS)

    def test_tool_names_are_unique(self):
        """Tool names in the registry must be strictly unique."""
        names = list(TOOL_REGISTRY.keys())
        self.assertEqual(len(names), len(set(names)))

    def test_tool_schemas_structure_and_parameters(self):
        """Tool schemas must match LLM function declaration format and contain expected parameters."""
        schemas = get_tool_schemas()
        self.assertEqual(len(schemas), 10)

        schema_map = {s["name"]: s for s in schemas}

        # Verify get_cpi_history schema
        history_schema = schema_map["get_cpi_history"]
        self.assertIn("start_date", history_schema["parameters"]["properties"])
        self.assertIn("end_date", history_schema["parameters"]["properties"])
        self.assertEqual(set(history_schema["parameters"]["required"]), {"start_date", "end_date"})

        # Verify compare_cpi_periods schema
        compare_schema = schema_map["compare_cpi_periods"]
        self.assertIn("current_date", compare_schema["parameters"]["properties"])
        self.assertIn("previous_date", compare_schema["parameters"]["properties"])
        self.assertEqual(set(compare_schema["parameters"]["required"]), {"current_date", "previous_date"})

        # Verify get_route_details schema
        route_schema = schema_map["get_route_details"]
        self.assertIn("route_id", route_schema["parameters"]["properties"])
        self.assertEqual(route_schema["parameters"]["required"], ["route_id"])

        # Confirm description exists for all
        for s in schemas:
            self.assertTrue(len(s["description"]) > 10, f"Description too short for {s['name']}")

    def test_dispatcher_calls_correct_function(self):
        """dispatch_tool() routes calls to the correct function and returns results."""
        row = (1, "2026-02-01", "2026-01-01", "national", None, None, 105.0, 500, None, "2026-02-01T10:00:00")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = dispatch_tool("get_latest_cpi", arguments={"index_type": "national"}, conn=mock_conn)

        self.assertIsNotNone(result)
        self.assertEqual(result["index_type"], "national")
        self.assertEqual(result["index_value"], 105.0)

    def test_dispatcher_unknown_tool_error(self):
        """dispatch_tool() returns structured error for non-existent tool names."""
        result = dispatch_tool("non_existent_tool", arguments={})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "unknown_tool")
        self.assertIn("Unknown tool", result["message"])

    def test_dispatcher_invalid_arguments_error(self):
        """dispatch_tool() returns structured error when invalid keyword args are passed."""
        result = dispatch_tool("get_latest_cpi", arguments={"invalid_param_foo": "bar"})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "invalid_arguments")
        self.assertIn("Invalid arguments", result["message"])

    def test_dispatcher_results_are_json_serializable(self):
        """Results returned by dispatch_tool() must be 100% JSON-serializable."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "DEL", "BOM", "Delhi", "Mumbai", 450000, True, "2026-01-01T00:00:00")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = dispatch_tool("get_route_details", arguments={"route_id": "DEL-BOM"}, conn=mock_conn)

        # Must not raise TypeError
        json_str = json.dumps(result)
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertEqual(str(parsed["route_id"]), "1")


if __name__ == "__main__":
    unittest.main()
