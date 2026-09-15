-- =====================================================================
-- SIH 2026 (PS 26056) — Airfare Price Index
-- Database schema: 5 tables (4 core + 1 optional)
-- Target: PostgreSQL (via Supabase)
--
-- Read this top to bottom with the team BEFORE the scraper writes
-- a single row. Every "why" comment exists because a wrong assumption
-- here breaks the statistics downstream.
-- =====================================================================


-- =====================================================================
-- TABLE 1: sources  (OPTIONAL but recommended)
-- One row per airline/OTA we scrape. Written once at setup, rarely changes.
-- =====================================================================
CREATE TABLE sources (
    source_id           SERIAL PRIMARY KEY,
    source_name         TEXT NOT NULL UNIQUE,        -- e.g. 'IndiGo Direct', 'MakeMyTrip'
    source_type         TEXT NOT NULL
                         CHECK (source_type IN ('airline_direct', 'ota')),
    base_url            TEXT,
    robots_txt_status   TEXT,                        -- what robots.txt allows, checked manually
    rate_limit_notes    TEXT,                        -- agreed polite-scraping pace for this source
    last_successful_scrape TIMESTAMPTZ,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE, -- flip to false if a source blocks us — don't delete history
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =====================================================================
-- TABLE 2: routes
-- One row per route we track. DGCA volume is here for ROUTE SELECTION
-- ONLY — never use it as a national-aggregation weight (see index_values).
-- =====================================================================
CREATE TABLE routes (
    route_id                    SERIAL PRIMARY KEY,
    origin_airport              CHAR(3) NOT NULL,     -- IATA code, e.g. 'DEL'
    destination_airport         CHAR(3) NOT NULL,
    origin_city                 TEXT NOT NULL,
    destination_city            TEXT NOT NULL,
    dgca_monthly_passenger_volume INTEGER,            -- for choosing WHICH routes to scrape only
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (origin_airport, destination_airport)
);


-- =====================================================================
-- TABLE 3: flight_observations
-- THE MOST IMPORTANT TABLE. One row per (flight, departure date,
-- scrape timestamp, source). This is what the scraper writes into,
-- and everything downstream (cleaning, Jevons, GEKS) reads from here.
--
-- Non-negotiable rule baked into this table: a repeated scrape of the
-- SAME flight at a DIFFERENT time is a NEW row, never an update to an
-- old one. The UNIQUE constraint at the bottom enforces this precisely —
-- it blocks true accidental re-inserts, but allows every genuinely
-- distinct timestamp through.
-- =====================================================================
CREATE TABLE flight_observations (
    observation_id          BIGSERIAL PRIMARY KEY,

    -- Identity: which route, which source, which flight
    route_id                INTEGER NOT NULL REFERENCES routes(route_id),
    source_id               INTEGER NOT NULL REFERENCES sources(source_id),
    airline_name            TEXT NOT NULL,
    flight_number           TEXT NOT NULL,

    -- Timing: the fields the whole project depends on getting right.
    -- scrape_timestamp = when WE looked.  departure_date/time = when the
    -- flight actually flies. These must NEVER be conflated.
    scrape_timestamp         TIMESTAMPTZ NOT NULL,
    departure_date           DATE NOT NULL,
    departure_time           TIME,

    -- lead_time_days is computed automatically so every team member's
    -- pipeline agrees on the same number — nobody has to calculate it by hand.
    lead_time_days           INTEGER GENERATED ALWAYS AS (
                                 departure_date - (scrape_timestamp AT TIME ZONE 'Asia/Kolkata')::date
                             ) STORED,

    -- advance_booking_window is set by the ingestion code (backend),
    -- bucketing lead_time_days into our sampling windows.
    advance_booking_window   TEXT
                             CHECK (advance_booking_window IN ('T+1','T+7','T+15','T+30','T+45', 'other')),

    -- Comparability: two prices are only "comparable" if these match.
    -- Don't let Jevons average a nonstop fare against a 1-stop fare.
    cabin_class              TEXT NOT NULL DEFAULT 'economy'
                             CHECK (cabin_class IN ('economy', 'premium_economy', 'business')),
    fare_family              TEXT,             -- saver / flexi / refundable — nullable, site-dependent
    stops                    SMALLINT NOT NULL DEFAULT 0,
    seat_availability_hint   TEXT,             -- e.g. "3 seats left" — nullable, best-effort

    -- Price: capture the whole AND the pieces. raw_price_displayed is
    -- the only field that must always be filled; everything else is
    -- filled whenever the site happens to expose it.
    raw_price_displayed      NUMERIC(10,2) NOT NULL,
    base_fare                NUMERIC(10,2),
    fuel_surcharge           NUMERIC(10,2),
    taxes_fees               NUMERIC(10,2),    -- UDF + PSF combined
    gst_amount               NUMERIC(10,2),
    convenience_fee          NUMERIC(10,2),    -- OTA-only, nullable
    currency                 TEXT NOT NULL DEFAULT 'INR',

    -- Status: the field that prevents sold-out fares from biasing the index.
    -- Set by the SCRAPER at collection time — it's the only one that knows.
    scrape_status             TEXT NOT NULL
                              CHECK (scrape_status IN ('observed', 'sold_out', 'scrape_failed', 'parse_error')),

    -- Provenance: the honesty tag. Every row gets one from the moment
    -- it's inserted — never added retroactively.
    data_provenance           TEXT NOT NULL
                              CHECK (data_provenance IN ('real_scraped', 'kaggle_seeded', 'synthetic')),

    -- Optional raw audit trail: keep the untouched scrape payload so we
    -- can re-derive the cleaned data later if cleaning rules change,
    -- without re-scraping. Nullable — only fill if storage allows.
    raw_payload_snapshot       JSONB,

    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- The core anti-duplication rule: same flight, same route, same
    -- source, same departure date, same scrape moment = one row only.
    -- Anything with a DIFFERENT scrape_timestamp is a new, valid row.
    UNIQUE (route_id, source_id, flight_number, departure_date, scrape_timestamp)
);

-- Indexes: flight_observations will be the largest, most-queried table.
CREATE INDEX idx_obs_route_date ON flight_observations (route_id, departure_date);
CREATE INDEX idx_obs_scrape_time ON flight_observations (scrape_timestamp);
CREATE INDEX idx_obs_window ON flight_observations (route_id, advance_booking_window);
CREATE INDEX idx_obs_status ON flight_observations (scrape_status);


-- =====================================================================
-- TABLE 4: data_quality_flags
-- A SIDE table, not an edit to flight_observations. Raw data is never
-- mutated or deleted — every quality decision is a separate, auditable
-- row pointing back at the observation it concerns.
-- =====================================================================
CREATE TABLE data_quality_flags (
    flag_id           BIGSERIAL PRIMARY KEY,
    observation_id    BIGINT NOT NULL REFERENCES flight_observations(observation_id),

    flag_type         TEXT NOT NULL
                      CHECK (flag_type IN (
                          'outlier_high', 'outlier_low', 'cross_source_mismatch',
                          'imputed', 'sold_out_excluded', 'confirmed_error',
                          'duplicate_suspected'
                      )),
    detected_by       TEXT NOT NULL DEFAULT 'rule_based'
                      CHECK (detected_by IN ('rule_based', 'ml_model')),
    flag_reason       TEXT,                       -- human-readable note for the audit trail
    reviewed_status   TEXT NOT NULL DEFAULT 'pending'
                      CHECK (reviewed_status IN ('pending', 'confirmed_real', 'confirmed_error')),

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_flags_observation ON data_quality_flags (observation_id);
CREATE INDEX idx_flags_status ON data_quality_flags (reviewed_status);


-- =====================================================================
-- TABLE 5: index_values
-- THE OUTPUT TABLE. Only the statistics engine writes here, and only
-- the API/dashboard ever reads from here — nothing downstream should
-- ever query flight_observations directly.
-- =====================================================================
CREATE TABLE index_values (
    index_id                  BIGSERIAL PRIMARY KEY,

    route_id                  INTEGER REFERENCES routes(route_id),  -- NULL = national-level index
    advance_booking_window    TEXT
                              CHECK (advance_booking_window IN ('T+1','T+7','T+15','T+30','T+45', 'all')),
    index_type                TEXT NOT NULL
                              CHECK (index_type IN ('jevons_elementary', 'geks_spliced', 'route_level', 'national')),

    index_date                DATE NOT NULL,        -- the date this index value represents
    base_period_date          DATE NOT NULL,        -- the reference point the index is relative to
    index_value                NUMERIC(10,4) NOT NULL,

    -- Transparency fields — how solid is this specific number?
    num_observations_used      INTEGER NOT NULL,
    data_provenance_mix        JSONB,               -- e.g. {"real_scraped": 8, "synthetic": 2}

    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (route_id, advance_booking_window, index_type, index_date)
);

CREATE INDEX idx_index_route_date ON index_values (route_id, index_date);
CREATE INDEX idx_index_type ON index_values (index_type);


-- =====================================================================
-- Quick reference: who writes to what
-- =====================================================================
-- sources                -> set up once by backend/DevOps at project start
-- routes                 -> set up once by backend, from DGCA route selection
-- flight_observations    -> written continuously by the SCRAPER (or DS/ML's
--                           synthetic generator, tagged accordingly)
-- data_quality_flags     -> written by DS/ML after reading fresh observations
-- index_values           -> written by DS/ML after running Jevons/GEKS
-- Dashboard/API          -> reads ONLY from index_values (and routes, for labels)
-- =====================================================================
