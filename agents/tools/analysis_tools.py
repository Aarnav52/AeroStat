"""
=============================================================================
AeroStat Granular Price Analysis Tools — Batch 2 (Deterministic)
=============================================================================
This module provides read-only, deterministic analytical tools that query
the 'cleaned_observations_table' and 'routes' database tables to analyze
airfare variations across routes, airlines, booking windows, and cabin classes.

Batch 2 Functions:
1. get_route_price_analysis()
2. get_airline_price_analysis()
3. get_booking_window_analysis()
4. get_cabin_analysis()

DATABASE SAFETY:
All functions execute READ-ONLY parameterized SQL queries.
No INSERT, UPDATE, DELETE, or DDL operations are performed.
=============================================================================
"""

from typing import Optional, Dict, Any, List
from agents.tools.cpi_tools import _get_connection, _validate_date_str


def get_route_price_analysis(
    observation_date: str,
    previous_date: Optional[str] = None,
    route_id: Optional[str] = None,
    conn=None,
) -> Dict[str, Any]:
    """
    Analyzes cleaned airfares grouped by route for a given observation date,
    optionally comparing metrics against a previous date.

    Parameters:
        observation_date: Primary observation date in YYYY-MM-DD format.
        previous_date: Optional comparison date in YYYY-MM-DD format.
        route_id: Optional route filter (numeric string e.g. "1" or code e.g. "DEL-BOM").
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing route fare statistics and period comparison results.
    """
    _validate_date_str(observation_date, "observation_date")
    if previous_date is not None:
        _validate_date_str(previous_date, "previous_date")

    def _fetch_route_stats(obs_date: str, active_conn) -> Dict[str, Dict[str, Any]]:
        query_parts = [
            """
            SELECT c.route_id::text,
                   r.origin_airport,
                   r.destination_airport,
                   r.origin_city,
                   r.destination_city,
                   AVG(c.clean_base_fare) AS avg_fare,
                   MIN(c.clean_base_fare) AS min_fare,
                   MAX(c.clean_base_fare) AS max_fare,
                   COUNT(*) AS num_observations
            FROM cleaned_observations_table c
            LEFT JOIN routes r ON c.route_id::text = r.route_id::text
            WHERE c.observation_date = %s
            """
        ]
        params: List[Any] = [obs_date]

        if route_id is not None:
            query_parts.append(
                "AND (c.route_id::text = %s OR (r.origin_airport || '-' || r.destination_airport) = %s)"
            )
            params.extend([str(route_id), str(route_id)])

        query_parts.append(
            "GROUP BY c.route_id::text, r.origin_airport, r.destination_airport, r.origin_city, r.destination_city"
        )
        query_parts.append("ORDER BY avg_fare DESC")
        sql = "\n".join(query_parts)

        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        results = {}
        for r in rows:
            r_id = r[0]
            results[r_id] = {
                "route_id": r_id,
                "origin_airport": r[1],
                "destination_airport": r[2],
                "origin_city": r[3],
                "destination_city": r[4],
                "avg_fare": round(float(r[5]), 2) if r[5] is not None else None,
                "min_fare": round(float(r[6]), 2) if r[6] is not None else None,
                "max_fare": round(float(r[7]), 2) if r[7] is not None else None,
                "num_observations": int(r[8]) if r[8] is not None else 0,
            }
        return results

    with _get_connection(conn) as active_conn:
        curr_stats = _fetch_route_stats(observation_date, active_conn)
        prev_stats = _fetch_route_stats(previous_date, active_conn) if previous_date else {}

    routes_output: List[Dict[str, Any]] = []

    if previous_date is None:
        for r_id, item in curr_stats.items():
            routes_output.append(item)
    else:
        all_route_ids = sorted(list(set(curr_stats.keys()).union(prev_stats.keys())))
        for r_id in all_route_ids:
            curr = curr_stats.get(r_id)
            prev = prev_stats.get(r_id)

            route_meta = curr or prev
            entry: Dict[str, Any] = {
                "route_id": r_id,
                "origin_airport": route_meta["origin_airport"],
                "destination_airport": route_meta["destination_airport"],
                "origin_city": route_meta["origin_city"],
                "destination_city": route_meta["destination_city"],
                "avg_fare": curr["avg_fare"] if curr else None,
                "min_fare": curr["min_fare"] if curr else None,
                "max_fare": curr["max_fare"] if curr else None,
                "num_observations": curr["num_observations"] if curr else 0,
                "previous_avg_fare": prev["avg_fare"] if prev else None,
                "previous_num_observations": prev["num_observations"] if prev else 0,
                "absolute_change": None,
                "percentage_change": None,
                "status": "compared",
            }

            if not curr:
                entry["status"] = "missing_current_observation"
            elif not prev:
                entry["status"] = "missing_previous_observation"
            else:
                c_avg = curr["avg_fare"]
                p_avg = prev["avg_fare"]
                if c_avg is not None and p_avg is not None:
                    abs_c = c_avg - p_avg
                    entry["absolute_change"] = round(abs_c, 2)
                    if p_avg == 0.0:
                        entry["percentage_change"] = None
                    else:
                        entry["percentage_change"] = round(((c_avg - p_avg) / p_avg) * 100.0, 4)

            routes_output.append(entry)

    status = "success" if routes_output else "no_observations_found"

    return {
        "observation_date": observation_date,
        "previous_date": previous_date,
        "route_id": route_id,
        "routes": routes_output,
        "status": status,
    }


def get_airline_price_analysis(
    observation_date: str,
    previous_date: Optional[str] = None,
    airline_code: Optional[str] = None,
    conn=None,
) -> Dict[str, Any]:
    """
    Analyzes cleaned airfares grouped by airline_code for a given observation date,
    optionally comparing metrics against a previous date.

    Parameters:
        observation_date: Primary observation date in YYYY-MM-DD format.
        previous_date: Optional comparison date in YYYY-MM-DD format.
        airline_code: Optional airline filter (e.g., "6E", "AI", "UK").
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing airline fare statistics and period comparison results.
    """
    _validate_date_str(observation_date, "observation_date")
    if previous_date is not None:
        _validate_date_str(previous_date, "previous_date")

    def _fetch_airline_stats(obs_date: str, active_conn) -> Dict[str, Dict[str, Any]]:
        query_parts = [
            """
            SELECT airline_code,
                   AVG(clean_base_fare) AS avg_fare,
                   MIN(clean_base_fare) AS min_fare,
                   MAX(clean_base_fare) AS max_fare,
                   COUNT(*) AS num_observations,
                   COUNT(DISTINCT route_id) AS routes_served_count
            FROM cleaned_observations_table
            WHERE observation_date = %s
            """
        ]
        params: List[Any] = [obs_date]

        if airline_code is not None:
            query_parts.append("AND airline_code = %s")
            params.append(airline_code)

        query_parts.append("GROUP BY airline_code ORDER BY avg_fare DESC")
        sql = "\n".join(query_parts)

        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        results = {}
        for r in rows:
            code = r[0]
            results[code] = {
                "airline_code": code,
                "avg_fare": round(float(r[1]), 2) if r[1] is not None else None,
                "min_fare": round(float(r[2]), 2) if r[2] is not None else None,
                "max_fare": round(float(r[3]), 2) if r[3] is not None else None,
                "num_observations": int(r[4]) if r[4] is not None else 0,
                "routes_served_count": int(r[5]) if r[5] is not None else 0,
            }
        return results

    with _get_connection(conn) as active_conn:
        curr_stats = _fetch_airline_stats(observation_date, active_conn)
        prev_stats = _fetch_airline_stats(previous_date, active_conn) if previous_date else {}

    airlines_output: List[Dict[str, Any]] = []

    if previous_date is None:
        for code, item in curr_stats.items():
            airlines_output.append(item)
    else:
        all_codes = sorted(list(set(curr_stats.keys()).union(prev_stats.keys())))
        for code in all_codes:
            curr = curr_stats.get(code)
            prev = prev_stats.get(code)

            entry: Dict[str, Any] = {
                "airline_code": code,
                "avg_fare": curr["avg_fare"] if curr else None,
                "min_fare": curr["min_fare"] if curr else None,
                "max_fare": curr["max_fare"] if curr else None,
                "num_observations": curr["num_observations"] if curr else 0,
                "routes_served_count": curr["routes_served_count"] if curr else (prev["routes_served_count"] if prev else 0),
                "previous_avg_fare": prev["avg_fare"] if prev else None,
                "previous_num_observations": prev["num_observations"] if prev else 0,
                "absolute_change": None,
                "percentage_change": None,
                "status": "compared",
            }

            if not curr:
                entry["status"] = "missing_current_observation"
            elif not prev:
                entry["status"] = "missing_previous_observation"
            else:
                c_avg = curr["avg_fare"]
                p_avg = prev["avg_fare"]
                if c_avg is not None and p_avg is not None:
                    abs_c = c_avg - p_avg
                    entry["absolute_change"] = round(abs_c, 2)
                    if p_avg == 0.0:
                        entry["percentage_change"] = None
                    else:
                        entry["percentage_change"] = round(((c_avg - p_avg) / p_avg) * 100.0, 4)

            airlines_output.append(entry)

    status = "success" if airlines_output else "no_observations_found"

    return {
        "observation_date": observation_date,
        "previous_date": previous_date,
        "airline_code": airline_code,
        "airlines": airlines_output,
        "status": status,
    }


def get_booking_window_analysis(
    observation_date: str,
    previous_date: Optional[str] = None,
    advance_booking_window: Optional[str] = None,
    conn=None,
) -> Dict[str, Any]:
    """
    Analyzes cleaned airfares grouped by advance_booking_window for a given observation date,
    optionally comparing metrics against a previous date.

    Parameters:
        observation_date: Primary observation date in YYYY-MM-DD format.
        previous_date: Optional comparison date in YYYY-MM-DD format.
        advance_booking_window: Optional booking window filter (e.g., "T+1", "T+7", "T+15", "T+30", "T+45").
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing booking window fare statistics and period comparison results.
    """
    _validate_date_str(observation_date, "observation_date")
    if previous_date is not None:
        _validate_date_str(previous_date, "previous_date")

    def _fetch_window_stats(obs_date: str, active_conn) -> Dict[str, Dict[str, Any]]:
        query_parts = [
            """
            SELECT advance_booking_window,
                   AVG(clean_base_fare) AS avg_fare,
                   MIN(clean_base_fare) AS min_fare,
                   MAX(clean_base_fare) AS max_fare,
                   COUNT(*) AS num_observations
            FROM cleaned_observations_table
            WHERE observation_date = %s
            """
        ]
        params: List[Any] = [obs_date]

        if advance_booking_window is not None:
            query_parts.append("AND advance_booking_window = %s")
            params.append(advance_booking_window)

        query_parts.append("GROUP BY advance_booking_window ORDER BY advance_booking_window ASC")
        sql = "\n".join(query_parts)

        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        results = {}
        for r in rows:
            win = r[0]
            results[win] = {
                "advance_booking_window": win,
                "avg_fare": round(float(r[1]), 2) if r[1] is not None else None,
                "min_fare": round(float(r[2]), 2) if r[2] is not None else None,
                "max_fare": round(float(r[3]), 2) if r[3] is not None else None,
                "num_observations": int(r[4]) if r[4] is not None else 0,
            }
        return results

    with _get_connection(conn) as active_conn:
        curr_stats = _fetch_window_stats(observation_date, active_conn)
        prev_stats = _fetch_window_stats(previous_date, active_conn) if previous_date else {}

    windows_output: List[Dict[str, Any]] = []

    if previous_date is None:
        for win, item in curr_stats.items():
            windows_output.append(item)
    else:
        all_windows = sorted(list(set(curr_stats.keys()).union(prev_stats.keys())))
        for win in all_windows:
            curr = curr_stats.get(win)
            prev = prev_stats.get(win)

            entry: Dict[str, Any] = {
                "advance_booking_window": win,
                "avg_fare": curr["avg_fare"] if curr else None,
                "min_fare": curr["min_fare"] if curr else None,
                "max_fare": curr["max_fare"] if curr else None,
                "num_observations": curr["num_observations"] if curr else 0,
                "previous_avg_fare": prev["avg_fare"] if prev else None,
                "previous_num_observations": prev["num_observations"] if prev else 0,
                "absolute_change": None,
                "percentage_change": None,
                "status": "compared",
            }

            if not curr:
                entry["status"] = "missing_current_observation"
            elif not prev:
                entry["status"] = "missing_previous_observation"
            else:
                c_avg = curr["avg_fare"]
                p_avg = prev["avg_fare"]
                if c_avg is not None and p_avg is not None:
                    abs_c = c_avg - p_avg
                    entry["absolute_change"] = round(abs_c, 2)
                    if p_avg == 0.0:
                        entry["percentage_change"] = None
                    else:
                        entry["percentage_change"] = round(((c_avg - p_avg) / p_avg) * 100.0, 4)

            windows_output.append(entry)

    status = "success" if windows_output else "no_observations_found"

    return {
        "observation_date": observation_date,
        "previous_date": previous_date,
        "advance_booking_window": advance_booking_window,
        "booking_windows": windows_output,
        "status": status,
    }


def get_cabin_analysis(
    observation_date: str,
    previous_date: Optional[str] = None,
    cabin_class: Optional[str] = None,
    conn=None,
) -> Dict[str, Any]:
    """
    Analyzes cleaned airfares grouped by cabin_class for a given observation date,
    optionally comparing metrics against a previous date.

    Parameters:
        observation_date: Primary observation date in YYYY-MM-DD format.
        previous_date: Optional comparison date in YYYY-MM-DD format.
        cabin_class: Optional cabin filter (e.g., "economy", "premium_economy", "business").
        conn: Optional existing database connection object.

    Returns:
        Dictionary containing cabin class fare statistics and period comparison results.
    """
    _validate_date_str(observation_date, "observation_date")
    if previous_date is not None:
        _validate_date_str(previous_date, "previous_date")

    def _fetch_cabin_stats(obs_date: str, active_conn) -> Dict[str, Dict[str, Any]]:
        query_parts = [
            """
            SELECT cabin_class,
                   AVG(clean_base_fare) AS avg_fare,
                   MIN(clean_base_fare) AS min_fare,
                   MAX(clean_base_fare) AS max_fare,
                   COUNT(*) AS num_observations
            FROM cleaned_observations_table
            WHERE observation_date = %s
            """
        ]
        params: List[Any] = [obs_date]

        if cabin_class is not None:
            query_parts.append("AND cabin_class = %s")
            params.append(cabin_class)

        query_parts.append("GROUP BY cabin_class ORDER BY avg_fare ASC")
        sql = "\n".join(query_parts)

        with active_conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        results = {}
        for r in rows:
            cab = r[0]
            results[cab] = {
                "cabin_class": cab,
                "avg_fare": round(float(r[1]), 2) if r[1] is not None else None,
                "min_fare": round(float(r[2]), 2) if r[2] is not None else None,
                "max_fare": round(float(r[3]), 2) if r[3] is not None else None,
                "num_observations": int(r[4]) if r[4] is not None else 0,
            }
        return results

    with _get_connection(conn) as active_conn:
        curr_stats = _fetch_cabin_stats(observation_date, active_conn)
        prev_stats = _fetch_cabin_stats(previous_date, active_conn) if previous_date else {}

    cabins_output: List[Dict[str, Any]] = []

    if previous_date is None:
        for cab, item in curr_stats.items():
            cabins_output.append(item)
    else:
        all_cabins = sorted(list(set(curr_stats.keys()).union(prev_stats.keys())))
        for cab in all_cabins:
            curr = curr_stats.get(cab)
            prev = prev_stats.get(cab)

            entry: Dict[str, Any] = {
                "cabin_class": cab,
                "avg_fare": curr["avg_fare"] if curr else None,
                "min_fare": curr["min_fare"] if curr else None,
                "max_fare": curr["max_fare"] if curr else None,
                "num_observations": curr["num_observations"] if curr else 0,
                "previous_avg_fare": prev["avg_fare"] if prev else None,
                "previous_num_observations": prev["num_observations"] if prev else 0,
                "absolute_change": None,
                "percentage_change": None,
                "status": "compared",
            }

            if not curr:
                entry["status"] = "missing_current_observation"
            elif not prev:
                entry["status"] = "missing_previous_observation"
            else:
                c_avg = curr["avg_fare"]
                p_avg = prev["avg_fare"]
                if c_avg is not None and p_avg is not None:
                    abs_c = c_avg - p_avg
                    entry["absolute_change"] = round(abs_c, 2)
                    if p_avg == 0.0:
                        entry["percentage_change"] = None
                    else:
                        entry["percentage_change"] = round(((c_avg - p_avg) / p_avg) * 100.0, 4)

            cabins_output.append(entry)

    status = "success" if cabins_output else "no_observations_found"

    return {
        "observation_date": observation_date,
        "previous_date": previous_date,
        "cabin_class": cabin_class,
        "cabins": cabins_output,
        "status": status,
    }
