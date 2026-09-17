"""
Deterministic Analytical Tools for AeroStat.
"""
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
from agents.tools.registry import (
    TOOL_REGISTRY,
    get_tool_registry,
    get_tool_schemas,
    dispatch_tool,
)

__all__ = [
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
    "TOOL_REGISTRY",
    "get_tool_registry",
    "get_tool_schemas",
    "dispatch_tool",
]
