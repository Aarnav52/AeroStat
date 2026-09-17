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

__all__ = [
    "get_latest_cpi",
    "get_cpi_history",
    "compare_cpi_periods",
    "get_route_price_analysis",
    "get_airline_price_analysis",
    "get_booking_window_analysis",
    "get_cabin_analysis",
]
