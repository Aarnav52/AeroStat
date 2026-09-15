"""Database persistence for the MVP pipeline. Credentials are loaded only from .env."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from .pipeline import (
    ALLOWED_STATUSES,
    build_cleaned_observations,
    detect_cross_source_mismatches,
    detect_duplicates,
    detect_outliers,
    generate_quality_flags,
    normalize_categories,
    profile_data,
    QualityIssue,
    recalculate_lead_time,
    validate_booking_window,
    validate_prices,
    validate_timestamps,
    validate_types,
)


def database_url() -> str:
    load_dotenv()
    if configured := os.getenv("DATABASE_URL"):
        return configured
    required = {key: os.getenv(key) for key in ("user", "password", "host", "port", "database")}
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing database configuration: {', '.join(missing)}")
    return "postgresql+psycopg://{user}:{password}@{host}:{port}/{database}".format(
        user=quote_plus(required["user"]), password=quote_plus(required["password"]), host=required["host"], port=required["port"], database=required["database"]
    )


def engine():
    return create_engine(database_url(), pool_pre_ping=True)


def apply_migration(connection, migration_path: Path) -> None:
    connection.execute(text(migration_path.read_text(encoding="utf-8")))


def _json_record(row: pd.Series) -> dict:
    return {key: (None if pd.isna(value) else str(value)) for key, value in row.items()}


def _insert_raw(connection, raw_frame: pd.DataFrame, source_file: str) -> dict[object, int]:
    raw_ids: dict[object, int] = {}
    raw_columns = list(raw_frame.columns)
    column_sql = ", ".join([*raw_columns, "source_file", "source_row_number"])
    value_sql = ", ".join([*(f":{column}" for column in raw_columns), ":source_file", ":source_row_number"])
    statement = text(f"""
        INSERT INTO flight_observations_raw ({column_sql}) VALUES ({value_sql})
        ON CONFLICT (source_file, source_row_number) DO UPDATE SET source_file = EXCLUDED.source_file
        RETURNING raw_id
    """)
    for row_number, (_, row) in enumerate(raw_frame.iterrows(), start=2):
        raw_id = connection.execute(statement, {**_json_record(row), "source_file": source_file, "source_row_number": row_number}).scalar_one()
        raw_ids[row.get("observation_id", row.name)] = raw_id
    return raw_ids


def _valid_for_structured_insert(row: pd.Series) -> bool:
    required = ["route_id", "source_id", "airline_name", "flight_number", "scrape_timestamp", "departure_date", "raw_price_displayed", "scrape_status", "data_provenance"]
    if any(pd.isna(row.get(column)) or row.get(column) == "" for column in required):
        return False
    return row["scrape_status"] in ALLOWED_STATUSES and row["cabin_class"] in {"economy", "premium_economy", "business"} and row["data_provenance"] in {"real_scraped", "kaggle_seeded", "synthetic"}


def _insert_structured(connection, frame: pd.DataFrame, raw_ids: dict[object, int]) -> dict[int, int]:
    statement = text("""
        INSERT INTO flight_observations (
          route_id, source_id, airline_name, flight_number, scrape_timestamp, departure_date, departure_time,
          advance_booking_window, cabin_class, fare_family, stops, seat_availability_hint, raw_price_displayed,
          base_fare, fuel_surcharge, taxes_fees, gst_amount, convenience_fee, currency, scrape_status,
          data_provenance, raw_payload_snapshot, created_at
        ) VALUES (
          :route_id, :source_id, :airline_name, :flight_number, :scrape_timestamp, :departure_date, :departure_time,
          :advance_booking_window, :cabin_class, :fare_family, :stops, :seat_availability_hint, :raw_price_displayed,
          :base_fare, :fuel_surcharge, :taxes_fees, :gst_amount, :convenience_fee, :currency, :scrape_status,
          :data_provenance, CAST(:raw_payload_snapshot AS jsonb), :created_at
        ) ON CONFLICT (route_id, source_id, flight_number, departure_date, scrape_timestamp) DO NOTHING
        RETURNING observation_id
    """)
    observation_ids: dict[int, int] = {}
    for _, row in frame.iterrows():
        if not _valid_for_structured_insert(row):
            continue
        values = row.to_dict()
        values["raw_payload_snapshot"] = row.get("raw_payload_snapshot") or None
        values["advance_booking_window"] = row.get("advance_booking_window") if row.get("advance_booking_window") in {"T+1", "T+7", "T+15", "T+30", "T+45", "other"} else "other"
        for key, value in list(values.items()):
            if pd.isna(value):
                values[key] = None
        observation_id = connection.execute(statement, values).scalar_one_or_none()
        raw_id = raw_ids[row.get("observation_id", row.name)]
        if observation_id is None:
            observation_id = connection.execute(text("""
                SELECT observation_id FROM flight_observations
                WHERE route_id = :route_id AND source_id = :source_id AND flight_number = :flight_number
                  AND departure_date = :departure_date AND scrape_timestamp = :scrape_timestamp
            """), values).scalar_one_or_none()
        if observation_id is not None:
            observation_ids[raw_id] = observation_id
    return observation_ids


def _insert_flags(connection, flags: pd.DataFrame, raw_ids: dict[object, int], observation_ids: dict[int, int]) -> int:
    statement = text("""
        INSERT INTO data_quality_flags (observation_id, raw_id, flag_type, detected_by, flag_reason, reviewed_status)
        VALUES (:observation_id, :raw_id, :flag_type, :detected_by, :flag_reason, :reviewed_status)
    """)
    count = 0
    for _, flag in flags.iterrows():
        raw_id = raw_ids.get(flag["row_key"])
        if raw_id is None:
            continue
        connection.execute(statement, {**flag.to_dict(), "observation_id": observation_ids.get(raw_id), "raw_id": raw_id})
        count += 1
    return count


def run_csv_pipeline(csv_path: Path, db_engine) -> dict:
    """Ingest one CSV source, retain raw records, and persist valid analytical outputs."""
    raw_frame = pd.read_csv(csv_path, dtype="string", keep_default_na=False)
    typed, type_issues = validate_types(raw_frame)
    normalized = normalize_categories(typed)
    enriched, lead_issues = recalculate_lead_time(normalized)
    sold_out = [
        QualityIssue(row.get("observation_id", row.name), "sold_out_excluded", "sold-out record excluded from price analytics")
        for _, row in enriched[enriched["scrape_status"] == "sold_out"].iterrows()
    ]
    issues = [type_issues, validate_timestamps(enriched), lead_issues, validate_booking_window(enriched), validate_prices(enriched), detect_duplicates(enriched), detect_outliers(enriched), detect_cross_source_mismatches(enriched), sold_out]
    flags = generate_quality_flags(issues)
    with db_engine.begin() as connection:
        raw_ids = _insert_raw(connection, raw_frame, csv_path.name)
        observation_ids = _insert_structured(connection, enriched, raw_ids)
        flag_count = _insert_flags(connection, flags, raw_ids, observation_ids)
    return {"profile": profile_data(raw_frame), "raw_rows": len(raw_frame), "structured_rows": len(observation_ids), "quality_flags": flag_count}
