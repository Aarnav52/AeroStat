from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.index_service import index_service

router = APIRouter()


@router.get("/")
def get_index(
    route: str = Query(..., description="Route code e.g. DEL-BOM"),
    window: str = Query(..., description="Booking window: T+1 or T+30"),
    base_date: Optional[str] = Query(None, description="Base date (YYYY-MM-DD). Defaults to earliest available."),
):
    """
    Returns the Jevons Price Index series for a route and booking window.
    """
    result = index_service.calculate_jevons_index(route, window, base_date)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/summary")
def get_index_summary(
    route: str = Query(..., description="Route code e.g. DEL-BOM"),
):
    """
    Returns Jevons index for all booking windows (T+1, T+30) in one call.
    Useful for dashboard summary cards.
    """
    result = index_service.calculate_cross_window_index(route)
    return result
