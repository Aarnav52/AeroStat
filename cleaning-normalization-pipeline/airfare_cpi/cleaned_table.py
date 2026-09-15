"""Create the canonical cleaned-observations table for Person B."""

import pandas as pd
from sqlalchemy import Date, Integer, Numeric, Text, text

CANONICAL_COLUMNS = [
    "observation_id", "observation_date", "route_id", "flight_number",
    "cabin_class", "advance_booking_window", "clean_base_fare", "data_provenance",
]


def prepare_cleaned_observations_table(cleaned_observations: pd.DataFrame) -> pd.DataFrame:
    """Map cleaned pipeline values to Person B's exact 8-column interface."""
    required_columns = [
        "observation_id", "observation_date", "route_id", "flight_number", "cabin_class",
        "advance_booking_window", "base_fare", "data_provenance", "scrape_status",
    ]
    missing_columns = [column for column in required_columns if column not in cleaned_observations.columns]
    if missing_columns:
        raise ValueError(f"cleaned_observations is missing: {', '.join(missing_columns)}")

    table = cleaned_observations.loc[
        cleaned_observations["scrape_status"].eq("observed") & cleaned_observations["base_fare"].notna(),
        required_columns,
    ].copy()
    table = table.rename(columns={"base_fare": "clean_base_fare"})
    table["observation_date"] = pd.to_datetime(table["observation_date"], errors="coerce").dt.date
    table["clean_base_fare"] = pd.to_numeric(table["clean_base_fare"], errors="coerce")
    return table[CANONICAL_COLUMNS]


def write_cleaned_observations_table(table: pd.DataFrame, db_engine) -> int:
    """Refresh the one canonical cleaned-observations table in Supabase."""

    if list(table.columns) != CANONICAL_COLUMNS:
        raise ValueError(f"table must contain exactly: {', '.join(CANONICAL_COLUMNS)}")

    with db_engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS cleaned_observations_table (
                observation_id TEXT,
                observation_date DATE,
                route_id INTEGER,
                flight_number TEXT,
                cabin_class TEXT,
                advance_booking_window TEXT,
                clean_base_fare NUMERIC(10,2),
                data_provenance TEXT
            )
        """))
        connection.execute(text("TRUNCATE TABLE cleaned_observations_table"))
        table.to_sql(
            "cleaned_observations_table", connection, if_exists="append", index=False, chunksize=500, method="multi",
            dtype={"observation_id": Text(), "observation_date": Date(), "route_id": Integer(), "clean_base_fare": Numeric(10, 2)},
        )
    return len(table)