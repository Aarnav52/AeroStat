from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.db.connection import get_db_connection

router = APIRouter()

@router.get("/")
def get_routes() -> List[Dict[str, Any]]:
    """
    Fetch all available routes from the database.
    """
    routes = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT route_id, origin_airport, destination_airport, origin_city, destination_city
                    FROM routes
                    WHERE is_active = true
                    ORDER BY route_id ASC
                    """
                )
                rows = cursor.fetchall()
                for row in rows:
                    routes.append({
                        "route_id": row[0],
                        "origin_airport": row[1],
                        "destination_airport": row[2],
                        "origin_city": row[3],
                        "destination_city": row[4],
                        "route_code": f"{row[1]}-{row[2]}"
                    })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return routes
