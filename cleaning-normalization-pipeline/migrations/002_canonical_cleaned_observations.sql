DROP TABLE IF EXISTS cleaned_observations;
DROP TABLE IF EXISTS cleaned_observations_table;

CREATE TABLE cleaned_observations_table (
    observation_id TEXT PRIMARY KEY,
    observation_date DATE NOT NULL,
    route_id INTEGER NOT NULL,
    flight_number TEXT NOT NULL,
    cabin_class TEXT NOT NULL,
    advance_booking_window TEXT NOT NULL,
    clean_base_fare NUMERIC(10,2) NOT NULL,
    data_provenance TEXT NOT NULL
);
