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
