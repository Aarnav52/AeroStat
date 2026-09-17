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
