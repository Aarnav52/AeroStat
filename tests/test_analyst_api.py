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
