"""Create the canonical cleaned-observations table for Person B (Jevons engine)."""

import pandas as pd

# ---------------------------------------------------------------------------
# Canonical airline IATA code mapping.
# Derived from the normalised airline_name produced by pipeline.normalize_categories().
# Add new airlines here; do NOT derive codes from flight_number prefixes.
# ---------------------------------------------------------------------------
AIRLINE_CODE_MAP: dict[str, str] = {
    "Air India": "AI",
    "IndiGo": "6E",
    "SpiceJet": "SG",
    "Akasa Air": "QP",
    "Fly 91": "91",
    "Vistara": "UK",
}

# Column order is the contract between the cleaning pipeline and the Jevons engine.
# The Jevons product-matching grain is:
#   (observation_date, route_id, airline_code, cabin_class, advance_booking_window)
CANONICAL_COLUMNS = [
    "observation_id",
    "observation_date",
    "route_id",
    "airline_code",
    "flight_number",
    "cabin_class",
    "advance_booking_window",
    "clean_base_fare",
    "data_provenance",
]


def prepare_cleaned_observations_table(cleaned_observations: pd.DataFrame) -> pd.DataFrame:
    """Map cleaned pipeline values to the canonical 9-column interface for the Jevons engine.

    Outlier detection operates on ``raw_price_displayed`` (the observable consumer-facing price).
    Index calculation uses ``clean_base_fare`` (the pre-tax base fare) — this distinction is
    intentional and methodologically defensible.
    """
    required_columns = [
        "observation_id",
        "observation_date",
        "route_id",
        "airline_name",      # used to derive airline_code
        "flight_number",
        "cabin_class",
        "advance_booking_window",
        "base_fare",
        "data_provenance",
        "scrape_status",
    ]
    missing_columns = [col for col in required_columns if col not in cleaned_observations.columns]
    if missing_columns:
        raise ValueError(f"cleaned_observations is missing: {', '.join(missing_columns)}")

    table = cleaned_observations.loc[
        cleaned_observations["scrape_status"].eq("observed") & cleaned_observations["base_fare"].notna(),
        required_columns,
    ].copy()

    # Rename base_fare → clean_base_fare
    table = table.rename(columns={"base_fare": "clean_base_fare"})

    # Derive airline_code from the normalised airline_name via explicit mapping.
    # Rows whose airline_name is not in the map are dropped (unknown airline).
    normalized_airlines = table["airline_name"].astype("string").str.strip().str.lower()
    normalized_airlines = normalized_airlines.str.replace(" ", "", regex=False)
    normalized_airline_map = {name.lower().replace(" ", ""): code for name, code in AIRLINE_CODE_MAP.items()}
    table["airline_code"] = normalized_airlines.map(normalized_airline_map)

    # Coerce types
    table["observation_date"] = pd.to_datetime(table["observation_date"], errors="coerce").dt.date
    table["clean_base_fare"] = pd.to_numeric(table["clean_base_fare"], errors="coerce")
    table["flight_number"] = table["flight_number"].astype("string").str.strip()

    valid_mask = (
        table["observation_id"].notna()
        & table["observation_date"].notna()
        & table["route_id"].notna()
        & table["airline_code"].notna()           # unknown airlines are excluded
        & table["flight_number"].notna()
        & table["flight_number"].ne("")
        & ~table["flight_number"].str.lower().isin(["nan", "none", "<na>"])
        & table["clean_base_fare"].notna()
        & (table["clean_base_fare"] > 0)
        & table["advance_booking_window"].isin(["T+1", "T+7", "T+15", "T+30", "T+45"])
    )
    table = table[valid_mask].copy()
    table = table.drop_duplicates(subset=["observation_id"])
    return table[CANONICAL_COLUMNS]


def write_cleaned_observations_table(table: pd.DataFrame, db_engine) -> int:
    """Refresh the one canonical cleaned-observations table in Supabase."""

    from sqlalchemy import Date, Integer, Numeric, Text, text

    if list(table.columns) != CANONICAL_COLUMNS:
        raise ValueError(f"table must contain exactly: {', '.join(CANONICAL_COLUMNS)}")

    with db_engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS cleaned_observations_table (
                observation_id TEXT PRIMARY KEY,
                observation_date DATE NOT NULL,
                route_id INTEGER NOT NULL,
                airline_code TEXT NOT NULL,
                flight_number TEXT NOT NULL,
                cabin_class TEXT NOT NULL,
                advance_booking_window TEXT NOT NULL,
                clean_base_fare NUMERIC(10,2) NOT NULL,
                data_provenance TEXT NOT NULL
            )
        """))
        connection.execute(text("TRUNCATE TABLE cleaned_observations_table"))
        table.to_sql(
            "cleaned_observations_table",
            connection,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi",
            dtype={
                "observation_id": Text(),
                "observation_date": Date(),
                "route_id": Integer(),
                "airline_code": Text(),
                "clean_base_fare": Numeric(10, 2),
            },
        )
    return len(table)
