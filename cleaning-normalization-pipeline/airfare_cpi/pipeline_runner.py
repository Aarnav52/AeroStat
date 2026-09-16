"""Connect the raw Supabase table, the cleaning functions, and Person B's table."""

import pandas as pd
from .cleaned_table import prepare_cleaned_observations_table, write_cleaned_observations_table
from .pipeline import (
    build_cleaned_observations,
    detect_cross_source_mismatches,
    detect_duplicates,
    detect_outliers,
    generate_quality_flags,
    normalize_categories,
    profile_data,
    recalculate_lead_time,
    validate_booking_window,
    validate_currency,
    validate_prices,
    validate_timestamps,
    validate_types,
)

# this function is used to run the cleaning pipeline on raw observations and return cleaned observations and quality flags. 
def clean_raw_observations(raw_observations: pd.DataFrame):
    """Run the existing cleaning functions and return cleaned observations plus flags."""
    typed_observations, type_issues = validate_types(raw_observations)
    typed_observations["observation_date"] = typed_observations["scrape_timestamp"].dt.tz_convert("Asia/Kolkata").dt.date
    normalized_observations = normalize_categories(typed_observations)
    enriched_observations, lead_time_issues = recalculate_lead_time(normalized_observations)
    timestamp_issues = validate_timestamps(enriched_observations)
    booking_window_issues = validate_booking_window(enriched_observations)
    currency_issues = validate_currency(enriched_observations)
    price_issues = validate_prices(enriched_observations)
    duplicate_issues = detect_duplicates(enriched_observations)
    outlier_issues = detect_outliers(enriched_observations)
    cross_source_issues = detect_cross_source_mismatches(enriched_observations)
    quality_flags = generate_quality_flags([
        type_issues,
        timestamp_issues,
        lead_time_issues,
        booking_window_issues,
        currency_issues,
        price_issues,
        duplicate_issues,
        outlier_issues,
        cross_source_issues,
    ])
    cleaned_observations = build_cleaned_observations(enriched_observations, quality_flags=quality_flags)
    return cleaned_observations, quality_flags


def read_raw_observations(db_engine) -> pd.DataFrame:
    """Read the raw landing table without modifying it."""
    return pd.read_sql("SELECT * FROM flight_observations_raw", db_engine)


def write_quality_flags(quality_flags: pd.DataFrame, raw_observations: pd.DataFrame, db_engine) -> int:
    """Store pending rule-based flags against the existing raw-table row ids."""
    from sqlalchemy import text

    if quality_flags.empty:
        return 0
    
    raw_ids = raw_observations[["raw_id", "observation_id"]].drop_duplicates("observation_id")
    flags_to_write = quality_flags.merge(raw_ids, left_on="row_key", right_on="observation_id", how="inner")
    if flags_to_write.empty:
        return 0

    with db_engine.begin() as connection:
        raw_id_values = flags_to_write["raw_id"].astype(int).tolist()
        connection.execute(text("""
            DELETE FROM data_quality_flags
            WHERE raw_id = ANY(:raw_ids) AND detected_by = 'rule_based' AND reviewed_status = 'pending'
        """), {"raw_ids": raw_id_values})
        flag_values = []
        for row_number, flag in flags_to_write.iterrows():
            flag_values.append({
                "raw_id": int(flag["raw_id"]),
                "flag_type": flag["flag_type"],
                "detected_by": flag["detected_by"],
                "flag_reason": flag["flag_reason"],
                "reviewed_status": flag["reviewed_status"],
            })
        connection.execute(text("""
            INSERT INTO data_quality_flags (raw_id, flag_type, detected_by, flag_reason, reviewed_status)
            VALUES (:raw_id, :flag_type, :detected_by, :flag_reason, :reviewed_status)
        """), flag_values)
    return len(flags_to_write)


def run_cleaning_pipeline(db_engine) -> dict:
    """Create Person B's table from the existing raw observation table."""
    raw_observations = read_raw_observations(db_engine)
    cleaned_observations, quality_flags = clean_raw_observations(raw_observations)
    person_b_table = prepare_cleaned_observations_table(cleaned_observations)
    flag_count = write_quality_flags(quality_flags, raw_observations, db_engine)
    table_count = write_cleaned_observations_table(person_b_table, db_engine)
    return {
        "raw_rows": len(raw_observations),
        "cleaned_rows": len(cleaned_observations),
        "quality_flags_written": flag_count,
        "person_b_rows": table_count,
        "profile": profile_data(raw_observations),
    }