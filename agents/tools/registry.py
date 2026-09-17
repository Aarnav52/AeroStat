"""
=============================================================================
AeroStat AI Analyst Tool Registry & Dispatcher
=============================================================================
This module provides a provider-agnostic registry and dispatcher interface for
all 10 deterministic CPI analyst tools.

Registered Tools (10 Total):
1. get_latest_cpi
2. get_cpi_history
3. compare_cpi_periods
4. get_route_price_analysis
5. get_airline_price_analysis
6. get_booking_window_analysis
7. get_cabin_analysis
8. get_data_quality_summary
9. get_supporting_observations
10. get_route_details

This module contains NO LLM API calls or credentials. It provides clean,
structured declarations and function dispatching for future LLM integration.
=============================================================================
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable

from agents.tools.cpi_tools import (
    get_latest_cpi,
    get_cpi_history,
    compare_cpi_periods,
)
from agents.tools.analysis_tools import (
    get_route_price_analysis,
    get_airline_price_analysis,
    get_booking_window_analysis,
    get_cabin_analysis,
)
from agents.tools.quality_and_meta_tools import (
    get_data_quality_summary,
    get_supporting_observations,
    get_route_details,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Represents a registered deterministic tool and its parameter schema."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


# =============================================================================
# Tool Definitions Registry
# =============================================================================

TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "get_latest_cpi": ToolDefinition(
        name="get_latest_cpi",
        description="Retrieve the most recent CPI/index observation from index_values data.",
        parameters={
            "type": "object",
            "properties": {
                "index_type": {
                    "type": "string",
                    "enum": ["national", "route", "elementary"],
                    "description": "Index granularity level. Defaults to 'national'.",
                },
                "route_id": {
                    "type": "string",
                    "description": "Optional route filter e.g. 'DEL-BOM' or '1'.",
                },
                "advance_booking_window": {
                    "type": "string",
                    "description": "Optional booking window filter e.g. 'T+1', 'T+7', 'T+15', 'T+30', 'T+45'.",
                },
            },
            "required": [],
        },
        function=get_latest_cpi,
    ),
    "get_cpi_history": ToolDefinition(
        name="get_cpi_history",
        description="Retrieve historical CPI/index observations for a requested date range in chronological order.",
        parameters={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Range start date in YYYY-MM-DD format (inclusive).",
                },
                "end_date": {
                    "type": "string",
                    "description": "Range end date in YYYY-MM-DD format (inclusive).",
                },
                "index_type": {
                    "type": "string",
                    "enum": ["national", "route", "elementary"],
                    "description": "Optional index granularity filter.",
                },
                "route_id": {
                    "type": "string",
                    "description": "Optional route filter e.g. 'DEL-BOM' or '1'.",
                },
                "advance_booking_window": {
                    "type": "string",
                    "description": "Optional booking window filter e.g. 'T+1', 'T+7'.",
                },
            },
            "required": ["start_date", "end_date"],
        },
        function=get_cpi_history,
    ),
    "compare_cpi_periods": ToolDefinition(
        name="compare_cpi_periods",
        description="Compare CPI/index observations between two dates and deterministically calculate absolute and percentage changes.",
        parameters={
            "type": "object",
            "properties": {
                "current_date": {
                    "type": "string",
                    "description": "Current observation date in YYYY-MM-DD format.",
                },
                "previous_date": {
                    "type": "string",
                    "description": "Comparison observation date in YYYY-MM-DD format.",
                },
                "index_type": {
                    "type": "string",
                    "enum": ["national", "route", "elementary"],
                    "description": "Optional index granularity filter. Defaults to 'national'.",
                },
                "route_id": {
                    "type": "string",
                    "description": "Optional route filter.",
                },
                "advance_booking_window": {
                    "type": "string",
                    "description": "Optional booking window filter.",
                },
            },
            "required": ["current_date", "previous_date"],
        },
        function=compare_cpi_periods,
    ),
    "get_route_price_analysis": ToolDefinition(
        name="get_route_price_analysis",
        description="Analyze cleaned airfares grouped by route for an observation date, optionally comparing against a previous date.",
        parameters={
            "type": "object",
            "properties": {
                "observation_date": {
                    "type": "string",
                    "description": "Primary observation date in YYYY-MM-DD format.",
                },
                "previous_date": {
                    "type": "string",
                    "description": "Optional comparison date in YYYY-MM-DD format.",
                },
                "route_id": {
                    "type": "string",
                    "description": "Optional route filter e.g. 'DEL-BOM' or '1'.",
                },
            },
            "required": ["observation_date"],
        },
        function=get_route_price_analysis,
    ),
    "get_airline_price_analysis": ToolDefinition(
        name="get_airline_price_analysis",
        description="Analyze cleaned airfares grouped by airline_code for an observation date, optionally comparing against a previous date.",
        parameters={
            "type": "object",
            "properties": {
                "observation_date": {
                    "type": "string",
                    "description": "Primary observation date in YYYY-MM-DD format.",
                },
                "previous_date": {
                    "type": "string",
                    "description": "Optional comparison date in YYYY-MM-DD format.",
                },
                "airline_code": {
                    "type": "string",
                    "description": "Optional airline code filter e.g. '6E', 'AI', 'UK'.",
                },
            },
            "required": ["observation_date"],
        },
        function=get_airline_price_analysis,
    ),
    "get_booking_window_analysis": ToolDefinition(
        name="get_booking_window_analysis",
        description="Analyze cleaned airfares grouped by advance_booking_window for an observation date, optionally comparing against a previous date.",
        parameters={
            "type": "object",
            "properties": {
                "observation_date": {
                    "type": "string",
                    "description": "Primary observation date in YYYY-MM-DD format.",
                },
                "previous_date": {
                    "type": "string",
                    "description": "Optional comparison date in YYYY-MM-DD format.",
                },
                "advance_booking_window": {
                    "type": "string",
                    "description": "Optional booking window filter e.g. 'T+1', 'T+7', 'T+15', 'T+30', 'T+45'.",
                },
            },
            "required": ["observation_date"],
        },
        function=get_booking_window_analysis,
    ),
    "get_cabin_analysis": ToolDefinition(
        name="get_cabin_analysis",
        description="Analyze cleaned airfares grouped by cabin_class for an observation date, optionally comparing against a previous date.",
        parameters={
            "type": "object",
            "properties": {
                "observation_date": {
                    "type": "string",
                    "description": "Primary observation date in YYYY-MM-DD format.",
                },
                "previous_date": {
                    "type": "string",
                    "description": "Optional comparison date in YYYY-MM-DD format.",
                },
                "cabin_class": {
                    "type": "string",
                    "description": "Optional cabin class filter e.g. 'economy', 'business'.",
                },
            },
            "required": ["observation_date"],
        },
        function=get_cabin_analysis,
    ),
    "get_data_quality_summary": ToolDefinition(
        name="get_data_quality_summary",
        description="Provide a factual summary of data availability, provenances, booking windows, cabin classes, and coverage stats.",
        parameters={
            "type": "object",
            "properties": {
                "observation_date": {
                    "type": "string",
                    "description": "Optional observation date filter in YYYY-MM-DD format.",
                },
            },
            "required": [],
        },
        function=get_data_quality_summary,
    ),
    "get_supporting_observations": ToolDefinition(
        name="get_supporting_observations",
        description="Retrieve actual cleaned flight observation records to serve as evidence for analytical findings.",
        parameters={
            "type": "object",
            "properties": {
                "route_id": {
                    "type": "string",
                    "description": "Optional route filter e.g. 'DEL-BOM' or '1'.",
                },
                "airline_code": {
                    "type": "string",
                    "description": "Optional airline code filter e.g. '6E', 'AI'.",
                },
                "observation_date": {
                    "type": "string",
                    "description": "Optional observation date filter in YYYY-MM-DD format.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default 50, range 1-1000).",
                },
            },
            "required": [],
        },
        function=get_supporting_observations,
    ),
    "get_route_details": ToolDefinition(
        name="get_route_details",
        description="Retrieve human-readable metadata for a specific route from the routes table.",
        parameters={
            "type": "object",
            "properties": {
                "route_id": {
                    "type": "string",
                    "description": "Route identifier e.g. numeric string '1' or airport pair code 'DEL-BOM'.",
                },
            },
            "required": ["route_id"],
        },
        function=get_route_details,
    ),
}


# =============================================================================
# Helper Functions & Dispatcher
# =============================================================================

def get_tool_registry() -> Dict[str, ToolDefinition]:
    """Returns the full dictionary of registered tool definitions."""
    return TOOL_REGISTRY


def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Returns provider-agnostic function declarations suitable for LLM function calling schemas.
    """
    schemas = []
    for tool_name, tool_def in sorted(TOOL_REGISTRY.items()):
        schemas.append({
            "name": tool_def.name,
            "description": tool_def.description,
            "parameters": tool_def.parameters,
        })
    return schemas


def dispatch_tool(
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    conn=None,
) -> Dict[str, Any]:
    """
    Dispatches a tool call by name with given arguments to its corresponding Python function.

    Parameters:
        tool_name: Name of the registered tool.
        arguments: Dictionary of arguments matching tool schema.
        conn: Optional database connection override (for testing/dependency injection).

    Returns:
        JSON-serializable result dictionary.
    """
    if tool_name not in TOOL_REGISTRY:
        available = sorted(list(TOOL_REGISTRY.keys()))
        return {
            "status": "error",
            "error_type": "unknown_tool",
            "message": f"Unknown tool: '{tool_name}'. Available tools: {available}",
        }

    tool_def = TOOL_REGISTRY[tool_name]
    kwargs = dict(arguments) if arguments is not None else {}

    if conn is not None:
        kwargs["conn"] = conn

    try:
        result = tool_def.function(**kwargs)
        # Verify JSON serializability
        json.dumps(result)
        return result
    except TypeError as e:
        return {
            "status": "error",
            "error_type": "invalid_arguments",
            "message": f"Invalid arguments for tool '{tool_name}': {str(e)}",
        }
    except ValueError as e:
        return {
            "status": "error",
            "error_type": "value_error",
            "message": str(e),
        }
    except Exception as e:
        logger.exception(f"Unexpected error executing tool '{tool_name}': {e}")
        return {
            "status": "error",
            "error_type": "execution_error",
            "message": f"Failed to execute tool '{tool_name}': {str(e)}",
        }
