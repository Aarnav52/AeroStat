"""
=============================================================================
AeroStat Quality & Evidence Tools — Batch 3 (Deterministic)
=============================================================================
This module provides read-only, deterministic analytical tools that query
the database to provide:
1. Factual data quality and coverage summaries (get_data_quality_summary).
2. Raw supporting flight observation records as evidence (get_supporting_observations).
3. Human-readable route metadata (get_route_details).

Batch 3 Functions:
1. get_data_quality_summary()
2. get_supporting_observations()
3. get_route_details()

DATABASE SAFETY:
All functions execute READ-ONLY parameterized SQL queries.
No INSERT, UPDATE, DELETE, or DDL operations are performed.
=============================================================================
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from agents.tools.cpi_tools import _get_connection, _validate_date_str

logger = logging.getLogger(__name__)


def get_data_quality_summary(
    observation_date: Optional[str] = None,
    conn=None,
) -> Dict[str, Any]:
    """
    Provides a deterministic, factual summary of the quality, coverage, and availability
    of airfare data in the database.

    Parameters:
        observation_date: Optional observation date filter in YYYY-MM-DD format.
                          If omitted, targets the latest available observation date.
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing factual counts, breakdowns, coverage stats, and explicit
        demarcation of unavailable/unmeasured metrics.
    """
    if observation_date is not None:
        _validate_date_str(observation_date, "observation_date")

    with _get_connection(conn) as active_conn:
        with active_conn.cursor() as cursor:
            # Determine target observation date if omitted
            target_date = observation_date
            if target_date is None:
                cursor.execute("SELECT MAX(observation_date) FROM cleaned_observations_table")
                max_row = cursor.fetchone()
                if max_row and max_row[0] is not None:
                    target_date = str(max_row[0])

            if target_date is None:
                # Database table is completely empty
                return {
                    "status": "no_observations_found",
                    "observation_date": None,
                    "measured_metrics": {
                        "total_observations": 0,
                        "unique_routes_count": 0,
                        "unique_airlines_count": 0,
                        "provenance_breakdown": {},
                        "booking_window_breakdown": {},
                        "cabin_class_breakdown": {},
                        "quality_flags_summary": {},
                        "overall_date_range": {"min_date": None, "max_date": None},
                    },
                    "unavailable_metrics": [
                        "representativeness_score",
                        "unmeasured_market_bias",
                        "unobserved_flight_fares",
                    ],
                }

            # 1. Total observations for target_date
            cursor.execute(
                "SELECT COUNT(*) FROM cleaned_observations_table WHERE observation_date = %s",
                (target_date,),
            )
            total_obs = cursor.fetchone()[0]

            # 2. Provenance breakdown
            cursor.execute(
                """
                SELECT data_provenance, COUNT(*)
                FROM cleaned_observations_table
                WHERE observation_date = %s
                GROUP BY data_provenance
                """,
                (target_date,),
            )
            provenance_breakdown = {row[0]: int(row[1]) for row in cursor.fetchall()}

            # 3. Booking window breakdown
            cursor.execute(
                """
                SELECT advance_booking_window, COUNT(*)
                FROM cleaned_observations_table
                WHERE observation_date = %s
                GROUP BY advance_booking_window
                ORDER BY advance_booking_window ASC
                """,
                (target_date,),
            )
            booking_window_breakdown = {row[0]: int(row[1]) for row in cursor.fetchall()}

            # 4. Cabin class breakdown
            cursor.execute(
                """
                SELECT cabin_class, COUNT(*)
                FROM cleaned_observations_table
                WHERE observation_date = %s
                GROUP BY cabin_class
                ORDER BY cabin_class ASC
                """,
                (target_date,),
            )
            cabin_class_breakdown = {row[0]: int(row[1]) for row in cursor.fetchall()}

            # 5. Unique routes & airlines count
            cursor.execute(
                """
                SELECT COUNT(DISTINCT route_id), COUNT(DISTINCT airline_code)
                FROM cleaned_observations_table
                WHERE observation_date = %s
                """,
                (target_date,),
            )
            unique_counts = cursor.fetchone()
            unique_routes = int(unique_counts[0]) if unique_counts else 0
            unique_airlines = int(unique_counts[1]) if unique_counts else 0

            # 6. Overall date range across cleaned_observations_table
            cursor.execute("SELECT MIN(observation_date), MAX(observation_date) FROM cleaned_observations_table")
            range_row = cursor.fetchone()
            min_d = str(range_row[0]) if range_row and range_row[0] is not None else None
            max_d = str(range_row[1]) if range_row and range_row[1] is not None else None

            # 7. Quality flags summary (safely query data_quality_flags table if present)
            quality_flags = {}
            try:
                cursor.execute(
                    """
                    SELECT flag_type, COUNT(*)
                    FROM data_quality_flags
                    GROUP BY flag_type
                    """
                )
                flag_rows = cursor.fetchall()
                if flag_rows:
                    quality_flags = {row[0]: int(row[1]) for row in flag_rows}
            except Exception as e:
                logger.debug(f"Could not query data_quality_flags: {e}")
                quality_flags = {}

    return {
        "status": "success",
        "observation_date": target_date,
        "measured_metrics": {
            "total_observations": total_obs,
            "unique_routes_count": unique_routes,
            "unique_airlines_count": unique_airlines,
            "provenance_breakdown": provenance_breakdown,
            "booking_window_breakdown": booking_window_breakdown,
            "cabin_class_breakdown": cabin_class_breakdown,
            "quality_flags_summary": quality_flags,
            "overall_date_range": {"min_date": min_d, "max_date": max_d},
        },
        "unavailable_metrics": [
            "representativeness_score",
            "unmeasured_market_bias",
            "unobserved_flight_fares",
        ],
    }


def get_supporting_observations(
    route_id: Optional[str] = None,
    airline_code: Optional[str] = None,
    observation_date: Optional[str] = None,
    limit: int = 50,
    conn=None,
) -> Dict[str, Any]:
    """
    Retrieves actual cleaned airfare observations to serve as verifiable evidence
    for analytical findings.

    Parameters:
        route_id: Optional route filter (e.g., "1" or "DEL-BOM").
        airline_code: Optional airline filter (e.g., "6E", "AI").
        observation_date: Optional observation date filter in YYYY-MM-DD format.
        limit: Maximum number of records to return (default 50, range 1-1000).
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing matching observation records and query filter details.
    """
    if observation_date is not None:
        _validate_date_str(observation_date, "observation_date")

    if not isinstance(limit, int) or limit < 1 or limit > 1000:
        raise ValueError(f"Invalid limit '{limit}': must be an integer between 1 and 1000.")

    query_parts = [
        """
        SELECT c.observation_id,
               c.observation_date,
               c.route_id::text,
               c.flight_number,
               c.airline_code,
               c.cabin_class,
               c.advance_booking_window,
               c.clean_base_fare,
               c.data_provenance
        FROM cleaned_observations_table c
        LEFT JOIN routes r ON c.route_id::text = r.route_id::text
        WHERE 1=1
        """
    ]
    params: List[Any] = []

    if observation_date is not None:
        query_parts.append("AND c.observation_date = %s")
        params.append(observation_date)

    if airline_code is not None:
        query_parts.append("AND c.airline_code = %s")
        params.append(airline_code)

    if route_id is not None:
        query_parts.append(
            "AND (c.route_id::text = %s OR (r.origin_airport || '-' || r.destination_airport) = %s)"
        )
        params.extend([str(route_id), str(route_id)])

    query_parts.append("ORDER BY c.observation_date DESC, c.clean_base_fare ASC LIMIT %s")
    params.append(limit)

    sql = "\n".join(query_parts)

    with _get_connection(conn) as active_conn:
        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

    observations: List[Dict[str, Any]] = []
    for r in rows:
        observations.append({
            "observation_id": str(r[0]),
            "observation_date": str(r[1]) if isinstance(r[1], (date, datetime)) else r[1],
            "route_id": str(r[2]),
            "flight_number": str(r[3]),
            "airline_code": str(r[4]),
            "cabin_class": str(r[5]),
            "advance_booking_window": str(r[6]),
            "clean_base_fare": round(float(r[7]), 2) if r[7] is not None else None,
            "data_provenance": str(r[8]),
        })

    status = "success" if observations else "no_observations_found"

    return {
        "query_filters": {
            "route_id": route_id,
            "airline_code": airline_code,
            "observation_date": observation_date,
            "limit": limit,
        },
        "count": len(observations),
        "observations": observations,
        "status": status,
    }


def get_route_details(
    route_id: str,
    conn=None,
) -> Dict[str, Any]:
    """
    Retrieves human-readable metadata for a specific flight route from the routes table.

    Parameters:
        route_id: Route identifier (e.g., numeric string "1" or code "DEL-BOM").
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing route origin/destination airports, cities, DGCA traffic, and status,
        or a missing-route result if the ID does not exist.
    """
    if route_id is None or str(route_id).strip() == "":
        raise ValueError("route_id must be provided as a non-empty string or integer.")

    sql = """
        SELECT route_id::text,
               origin_airport,
               destination_airport,
               origin_city,
               destination_city,
               dgca_monthly_passenger_volume,
               is_active,
               created_at
        FROM routes
        WHERE route_id::text = %s OR (origin_airport || '-' || destination_airport) = %s
        LIMIT 1
    """

    r_str = str(route_id).strip()

    with _get_connection(conn) as active_conn:
        with active_conn.cursor() as cursor:
            cursor.execute(sql, (r_str, r_str))
            row = cursor.fetchone()

    if not row:
        return {
            "status": "route_not_found",
            "route_id": r_str,
            "message": f"Route '{r_str}' not found in database.",
        }

    return {
        "status": "success",
        "route_id": row[0],
        "origin_airport": row[1],
        "destination_airport": row[2],
        "origin_city": row[3],
        "destination_city": row[4],
        "dgca_monthly_passenger_volume": int(row[5]) if row[5] is not None else None,
        "is_active": bool(row[6]) if row[6] is not None else True,
        "created_at": (
            row[7].isoformat()
            if hasattr(row[7], "isoformat")
            else (str(row[7]) if row[7] is not None else None)
        ),
    }
