DROP TABLE IF EXISTS cleaned_observations;
DROP TABLE IF EXISTS cleaned_observations_table;

CREATE TABLE cleaned_observations_table (
    observation_id TEXT,
    observation_date DATE,
    route_id INTEGER,
    airline_code TEXT,
    cabin_class TEXT,
    advance_booking_window TEXT,
    clean_base_fare NUMERIC(10,2),
    data_provenance TEXT
);
