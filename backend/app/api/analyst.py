"""
=============================================================================
AeroStat Analyst API Router (backend/app/api/analyst.py)
=============================================================================
This router connects the FastAPI backend to the deterministic tool registry,
exposing analyst tool schemas and execution endpoints to the API layer.
=============================================================================
"""

import os
import sys
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Ensure workspace root is in sys.path to import agents package
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from agents.tools.registry import get_tool_schemas, dispatch_tool, TOOL_REGISTRY

router = APIRouter()


# =============================================================================
# Request Models
# =============================================================================

class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Optional[Dict[str, Any]] = None


class CPIComparisonRequest(BaseModel):
    current_date: str
    previous_date: str
    index_type: Optional[str] = "national"
    route_id: Optional[str] = None
    advance_booking_window: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def _handle_tool_result(result: Any):
    if isinstance(result, dict) and result.get("status") == "error":
        error_type = result.get("error_type", "")
        msg = result.get("message", "Tool execution error")
        if error_type == "unknown_tool":
            raise HTTPException(status_code=404, detail=msg)
        elif error_type in ("invalid_arguments", "value_error"):
            raise HTTPException(status_code=400, detail=msg)
        else:
            raise HTTPException(status_code=500, detail=msg)
    return result


# =============================================================================
# Registry & Execution Endpoints
# =============================================================================

@router.get("/tools")
def list_analyst_tools() -> List[Dict[str, Any]]:
    """
    Returns declarations and JSON schemas for all registered deterministic analyst tools.
    """
    return get_tool_schemas()


@router.post("/tools/execute")
def execute_analyst_tool(req: ToolExecutionRequest):
    """
    Executes a specific analyst tool by name with arguments via the tool registry dispatcher.
    """
    if not req.tool_name or req.tool_name not in TOOL_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tool: '{req.tool_name}'. Available tools: {sorted(list(TOOL_REGISTRY.keys()))}",
        )
    result = dispatch_tool(req.tool_name, req.arguments or {})
    return _handle_tool_result(result)


# =============================================================================
# Direct Tool Endpoint Wrappers
# =============================================================================

@router.get("/cpi/latest")
def get_latest_cpi_endpoint(
    index_type: Optional[str] = Query("national", description="Index type: national, route, or elementary"),
    route_id: Optional[str] = Query(None, description="Optional route filter e.g. DEL-BOM or 1"),
    advance_booking_window: Optional[str] = Query(None, description="Optional window filter e.g. T+1"),
):
    args = {}
    if index_type is not None:
        args["index_type"] = index_type
    if route_id is not None:
        args["route_id"] = route_id
    if advance_booking_window is not None:
        args["advance_booking_window"] = advance_booking_window

    result = dispatch_tool("get_latest_cpi", args)
    return _handle_tool_result(result)


@router.get("/cpi/history")
def get_cpi_history_endpoint(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    index_type: Optional[str] = Query(None, description="Optional index type filter"),
    route_id: Optional[str] = Query(None, description="Optional route filter"),
    advance_booking_window: Optional[str] = Query(None, description="Optional window filter"),
):
    args = {"start_date": start_date, "end_date": end_date}
    if index_type is not None:
        args["index_type"] = index_type
    if route_id is not None:
        args["route_id"] = route_id
    if advance_booking_window is not None:
        args["advance_booking_window"] = advance_booking_window

    result = dispatch_tool("get_cpi_history", args)
    return _handle_tool_result(result)


@router.post("/cpi/compare")
def compare_cpi_periods_endpoint(req: CPIComparisonRequest):
    args = {
        "current_date": req.current_date,
        "previous_date": req.previous_date,
    }
    if req.index_type is not None:
        args["index_type"] = req.index_type
    if req.route_id is not None:
        args["route_id"] = req.route_id
    if req.advance_booking_window is not None:
        args["advance_booking_window"] = req.advance_booking_window

    result = dispatch_tool("compare_cpi_periods", args)
    return _handle_tool_result(result)


@router.get("/analysis/routes")
def get_route_price_analysis_endpoint(
    observation_date: str = Query(..., description="Observation date in YYYY-MM-DD format"),
    previous_date: Optional[str] = Query(None, description="Optional comparison date"),
    route_id: Optional[str] = Query(None, description="Optional route filter"),
):
    args = {"observation_date": observation_date}
    if previous_date is not None:
        args["previous_date"] = previous_date
    if route_id is not None:
        args["route_id"] = route_id

    result = dispatch_tool("get_route_price_analysis", args)
    return _handle_tool_result(result)


@router.get("/analysis/airlines")
def get_airline_price_analysis_endpoint(
    observation_date: str = Query(..., description="Observation date in YYYY-MM-DD format"),
    previous_date: Optional[str] = Query(None, description="Optional comparison date"),
    airline_code: Optional[str] = Query(None, description="Optional airline code filter"),
):
    args = {"observation_date": observation_date}
    if previous_date is not None:
        args["previous_date"] = previous_date
    if airline_code is not None:
        args["airline_code"] = airline_code

    result = dispatch_tool("get_airline_price_analysis", args)
    return _handle_tool_result(result)


@router.get("/analysis/booking-windows")
def get_booking_window_analysis_endpoint(
    observation_date: str = Query(..., description="Observation date in YYYY-MM-DD format"),
    previous_date: Optional[str] = Query(None, description="Optional comparison date"),
    advance_booking_window: Optional[str] = Query(None, description="Optional window filter"),
):
    args = {"observation_date": observation_date}
    if previous_date is not None:
        args["previous_date"] = previous_date
    if advance_booking_window is not None:
        args["advance_booking_window"] = advance_booking_window

    result = dispatch_tool("get_booking_window_analysis", args)
    return _handle_tool_result(result)


@router.get("/analysis/cabins")
def get_cabin_analysis_endpoint(
    observation_date: str = Query(..., description="Observation date in YYYY-MM-DD format"),
    previous_date: Optional[str] = Query(None, description="Optional comparison date"),
    cabin_class: Optional[str] = Query(None, description="Optional cabin class filter"),
):
    args = {"observation_date": observation_date}
    if previous_date is not None:
        args["previous_date"] = previous_date
    if cabin_class is not None:
        args["cabin_class"] = cabin_class

    result = dispatch_tool("get_cabin_analysis", args)
    return _handle_tool_result(result)


@router.get("/quality")
def get_data_quality_summary_endpoint(
    observation_date: Optional[str] = Query(None, description="Optional observation date filter"),
):
    args = {}
    if observation_date is not None:
        args["observation_date"] = observation_date

    result = dispatch_tool("get_data_quality_summary", args)
    return _handle_tool_result(result)


@router.get("/observations")
def get_supporting_observations_endpoint(
    route_id: Optional[str] = Query(None, description="Optional route filter"),
    airline_code: Optional[str] = Query(None, description="Optional airline filter"),
    observation_date: Optional[str] = Query(None, description="Optional observation date filter"),
    limit: Optional[int] = Query(50, description="Max records to return (1-1000)"),
):
    args = {}
    if route_id is not None:
        args["route_id"] = route_id
    if airline_code is not None:
        args["airline_code"] = airline_code
    if observation_date is not None:
        args["observation_date"] = observation_date
    if limit is not None:
        args["limit"] = limit

    result = dispatch_tool("get_supporting_observations", args)
    return _handle_tool_result(result)


@router.get("/routes/{route_id}")
def get_route_details_endpoint(
    route_id: str,
):
    args = {"route_id": route_id}
    result = dispatch_tool("get_route_details", args)
    if isinstance(result, dict) and result.get("status") == "route_not_found":
        raise HTTPException(status_code=404, detail=result.get("message", f"Route {route_id} not found"))
    return _handle_tool_result(result)
