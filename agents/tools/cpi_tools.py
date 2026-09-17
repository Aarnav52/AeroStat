"""
=============================================================================
AeroStat CPI Analytical Tools — Batch 1 (Deterministic)
=============================================================================
This module provides read-only, deterministic analytical tools that query
the pre-computed 'index_values' database table. These tools are designed
for consumption by future LLM Analyst Agents or human analysts.

Batch 1 Functions:
1. get_latest_cpi()
2. get_cpi_history()
3. compare_cpi_periods()

DATABASE SAFETY:
All functions execute READ-ONLY parameterized SQL queries.
No INSERT, UPDATE, DELETE, or DDL operations are performed.
=============================================================================
"""

import os
import sys
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from contextlib import nullcontext

# Ensure backend package path is accessible regardless of execution environment
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from app.db.connection import get_db_connection


def _get_connection(conn=None):
    """
    Returns a context manager providing a database connection.
    Reuses existing connection if passed, otherwise opens a new one via get_db_connection().
    """
    if conn is not None:
        return nullcontext(conn)
    return get_db_connection()


def _row_to_dict(row) -> Dict[str, Any]:
    """
    Converts a database tuple from index_values into a structured dictionary.
    """
    if not row:
        return {}
    return {
        "id": row[0],
        "observation_date": str(row[1]) if isinstance(row[1], (date, datetime)) else row[1],
        "base_period_date": str(row[2]) if isinstance(row[2], (date, datetime)) else row[2],
        "index_type": row[3],
        "route_id": row[4],
        "advance_booking_window": row[5],
        "index_value": float(row[6]) if row[6] is not None else None,
        "num_observations_used": int(row[7]) if row[7] is not None else 0,
        "data_provenance_mix": row[8],
        "calculated_at": (
            row[9].isoformat()
            if hasattr(row[9], "isoformat")
            else (str(row[9]) if row[9] is not None else None)
        ),
    }


def _validate_date_str(date_str: str, param_name: str) -> date:
    """
    Validates that a string is a valid YYYY-MM-DD date.
    Raises ValueError if formatting is invalid.
    """
    if not isinstance(date_str, str):
        raise ValueError(f"Invalid {param_name}: must be a string in YYYY-MM-DD format.")
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid {param_name}: '{date_str}'. Expected format YYYY-MM-DD.")


def get_latest_cpi(
    index_type: Optional[str] = "national",
    route_id: Optional[str] = None,
    advance_booking_window: Optional[str] = None,
    conn=None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent CPI/index observation from the index_values table.

    Parameters:
        index_type: Filter by 'national', 'route', or 'elementary'. Defaults to 'national'.
                    Set to None to query across all index types.
        route_id: Optional route filter e.g. "DEL-BOM" or "1".
        advance_booking_window: Optional booking window filter e.g. "T+1", "T+7", "T+30".
        conn: Optional existing database connection object (used for dependency injection/tests).

    Returns:
        A dictionary containing the latest index observation, or None if no matching records exist.
    """
    query_parts = [
        """
        SELECT id, observation_date, base_period_date, index_type,
               route_id, advance_booking_window, index_value,
               num_observations_used, data_provenance_mix, calculated_at
        FROM index_values
        WHERE 1=1
        """
    ]
    params: List[Any] = []

    if index_type is not None:
        query_parts.append("AND index_type = %s")
        params.append(index_type)

    if route_id is not None:
        query_parts.append("AND route_id = %s")
        params.append(str(route_id))

    if advance_booking_window is not None:
        query_parts.append("AND advance_booking_window = %s")
        params.append(advance_booking_window)

    query_parts.append("ORDER BY observation_date DESC, calculated_at DESC, id DESC LIMIT 1")
    sql = "\n".join(query_parts)

    with _get_connection(conn) as active_conn:
        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            row = cursor.fetchone()

    if not row:
        return None
    return _row_to_dict(row)


def get_cpi_history(
    start_date: str,
    end_date: str,
    index_type: Optional[str] = None,
    route_id: Optional[str] = None,
    advance_booking_window: Optional[str] = None,
    conn=None,
) -> List[Dict[str, Any]]:
    """
    Retrieves historical CPI/index observations for a requested date range in chronological order.

    Parameters:
        start_date: Range start date in YYYY-MM-DD format (inclusive).
        end_date: Range end date in YYYY-MM-DD format (inclusive).
        index_type: Optional filter by 'national', 'route', or 'elementary'.
        route_id: Optional route filter e.g. "DEL-BOM" or "1".
        advance_booking_window: Optional booking window filter e.g. "T+1", "T+7", "T+30".
        conn: Optional existing database connection object.

    Returns:
        List of observation dictionaries ordered chronologically by observation_date ASC.
        Returns [] if no matching records exist.
    """
    parsed_start = _validate_date_str(start_date, "start_date")
    parsed_end = _validate_date_str(end_date, "end_date")

    if parsed_start > parsed_end:
        raise ValueError(
            f"Invalid date range: start_date '{start_date}' is after end_date '{end_date}'."
        )

    query_parts = [
        """
        SELECT id, observation_date, base_period_date, index_type,
               route_id, advance_booking_window, index_value,
               num_observations_used, data_provenance_mix, calculated_at
        FROM index_values
        WHERE observation_date >= %s AND observation_date <= %s
        """
    ]
    params: List[Any] = [parsed_start, parsed_end]

    if index_type is not None:
        query_parts.append("AND index_type = %s")
        params.append(index_type)

    if route_id is not None:
        query_parts.append("AND route_id = %s")
        params.append(str(route_id))

    if advance_booking_window is not None:
        query_parts.append("AND advance_booking_window = %s")
        params.append(advance_booking_window)

    query_parts.append("ORDER BY observation_date ASC, calculated_at ASC, id ASC")
    sql = "\n".join(query_parts)

    with _get_connection(conn) as active_conn:
        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

    return [_row_to_dict(r) for r in rows] if rows else []


def compare_cpi_periods(
    current_date: str,
    previous_date: str,
    index_type: Optional[str] = "national",
    route_id: Optional[str] = None,
    advance_booking_window: Optional[str] = None,
    conn=None,
) -> Dict[str, Any]:
    """
    Compares CPI/index observations between two dates and deterministically calculates:
    - current index value
    - previous index value
    - absolute change (current_value - previous_value)
    - percentage change (((current_value - previous_value) / previous_value) * 100)

    Handles zero-division, missing data, and identical dates explicitly.

    Parameters:
        current_date: Current observation date in YYYY-MM-DD format.
        previous_date: Comparison observation date in YYYY-MM-DD format.
        index_type: Optional filter by 'national', 'route', or 'elementary'. Defaults to 'national'.
        route_id: Optional route filter.
        advance_booking_window: Optional booking window filter.
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing comparison results and calculated metadata.
    """
    _validate_date_str(current_date, "current_date")
    _validate_date_str(previous_date, "previous_date")

    def _fetch_single_observation(obs_date: str, active_conn) -> Optional[Dict[str, Any]]:
        query_parts = [
            """
            SELECT id, observation_date, base_period_date, index_type,
                   route_id, advance_booking_window, index_value,
                   num_observations_used, data_provenance_mix, calculated_at
            FROM index_values
            WHERE observation_date = %s
            """
        ]
        params: List[Any] = [obs_date]

        if index_type is not None:
            query_parts.append("AND index_type = %s")
            params.append(index_type)

        if route_id is not None:
            query_parts.append("AND route_id = %s")
            params.append(str(route_id))

        if advance_booking_window is not None:
            query_parts.append("AND advance_booking_window = %s")
            params.append(advance_booking_window)

        query_parts.append("ORDER BY calculated_at DESC, id DESC LIMIT 1")
        sql = "\n".join(query_parts)

        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            row = cursor.fetchone()
        return _row_to_dict(row) if row else None

    with _get_connection(conn) as active_conn:
        current_obs = _fetch_single_observation(current_date, active_conn)
        previous_obs = _fetch_single_observation(previous_date, active_conn)

    # Base result structure
    result: Dict[str, Any] = {
        "current_date": current_date,
        "previous_date": previous_date,
        "index_type": index_type,
        "route_id": route_id,
        "advance_booking_window": advance_booking_window,
        "current_observation": current_obs,
        "previous_observation": previous_obs,
        "current_value": current_obs["index_value"] if current_obs else None,
        "previous_value": previous_obs["index_value"] if previous_obs else None,
        "absolute_change": None,
        "percentage_change": None,
        "percentage_change_status": "ok",
        "status": "success",
    }

    # Handle missing observation(s)
    if not current_obs or not previous_obs:
        if not current_obs and not previous_obs:
            result["status"] = "missing_both_observations"
            result["percentage_change_status"] = "missing_both_observations"
        elif not current_obs:
            result["status"] = "missing_current_observation"
            result["percentage_change_status"] = "missing_current_observation"
        else:
            result["status"] = "missing_previous_observation"
            result["percentage_change_status"] = "missing_previous_observation"
        return result

    curr_val = current_obs["index_value"]
    prev_val = previous_obs["index_value"]

    if curr_val is None or prev_val is None:
        result["status"] = "null_index_value"
        result["percentage_change_status"] = "null_index_value"
        return result

    # Handle identical dates
    if current_date == previous_date:
        result["absolute_change"] = 0.0
        result["percentage_change"] = 0.0
        result["percentage_change_status"] = "same_date"
        return result

    # Deterministic calculations
    abs_change = curr_val - prev_val
    result["absolute_change"] = round(abs_change, 4)

    if prev_val == 0.0:
        result["percentage_change"] = None
        result["percentage_change_status"] = "undefined_division_by_zero"
    else:
        pct_change = ((curr_val - prev_val) / prev_val) * 100.0
        result["percentage_change"] = round(pct_change, 4)
        result["percentage_change_status"] = "ok"

    return result
