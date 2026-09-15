CREATE TABLE IF NOT EXISTS flight_observations_raw (
    raw_id BIGSERIAL PRIMARY KEY,
    observation_id TEXT, route_id TEXT, source_id TEXT, airline_name TEXT, flight_number TEXT,
    scrape_timestamp TEXT, departure_date TEXT, departure_time TEXT, lead_time_days TEXT,
    advance_booking_window TEXT, cabin_class TEXT, fare_family TEXT, stops TEXT,
    seat_availability_hint TEXT, raw_price_displayed TEXT, base_fare TEXT, fuel_surcharge TEXT,
    taxes_fees TEXT, gst_amount TEXT, convenience_fee TEXT, currency TEXT, scrape_status TEXT,
    data_provenance TEXT, raw_payload_snapshot TEXT, created_at TEXT, loaded_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE flight_observations_raw ADD COLUMN IF NOT EXISTS source_file TEXT;
ALTER TABLE flight_observations_raw ADD COLUMN IF NOT EXISTS source_row_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_source_row ON flight_observations_raw (source_file, source_row_number);

ALTER TABLE data_quality_flags ADD COLUMN IF NOT EXISTS raw_id BIGINT REFERENCES flight_observations_raw(raw_id);
ALTER TABLE data_quality_flags ALTER COLUMN observation_id DROP NOT NULL;
ALTER TABLE data_quality_flags DROP CONSTRAINT IF EXISTS data_quality_flags_has_subject;
ALTER TABLE data_quality_flags ADD CONSTRAINT data_quality_flags_has_subject CHECK (observation_id IS NOT NULL OR raw_id IS NOT NULL);

CREATE TABLE IF NOT EXISTS cleaned_observations_table (
    observation_id TEXT,
    observation_date DATE,
    route_id INTEGER,
    airline_code TEXT,
    cabin_class TEXT,
    advance_booking_window TEXT,
    clean_base_fare NUMERIC(10,2),
    data_provenance TEXT
);
