import pandas as pd
import unittest

from airfare_cpi.pipeline import (
    build_cleaned_observations,
    detect_duplicates,
    detect_outliers,
    normalize_categories,
    recalculate_lead_time,
    validate_booking_window,
    validate_prices,
    validate_types,
)
from airfare_cpi.cleaned_table import CANONICAL_COLUMNS, prepare_cleaned_observations_table
from airfare_cpi.pipeline_runner import clean_raw_observations


def record(**overrides):
    row = {
        "observation_id": 1, "route_id": "1", "source_id": "1", "airline_name": " Air India ",
        "flight_number": "AI101", "scrape_timestamp": "2026-09-19T20:00:00+00:00",
        "departure_date": "2026-09-21", "departure_time": "10:00:00", "lead_time_days": "1",
        "advance_booking_window": " t+1 ", "cabin_class": "Economy", "fare_family": " Saver ",
        "stops": "0", "raw_price_displayed": "1000", "base_fare": "500", "fuel_surcharge": "100",
        "taxes_fees": "200", "gst_amount": "100", "convenience_fee": "100", "currency": " INR ",
        "scrape_status": "Observed", "data_provenance": "synthetic",
    }
    row.update(overrides)
    return row


def prepared(*rows):
    typed, _ = validate_types(pd.DataFrame(rows))
    return normalize_categories(typed)


class PipelineTests(unittest.TestCase):
    def test_type_conversion_and_category_normalization(self):
        frame = prepared(record())
        self.assertEqual(frame.loc[0, "route_id"], 1)
        self.assertEqual(frame.loc[0, "airline_name"], "Air India")
        self.assertEqual(frame.loc[0, "currency"], "INR")
        self.assertEqual(frame.loc[0, "advance_booking_window"], "T+1")

    def test_ist_lead_time_is_recalculated_and_mismatch_is_flagged(self):
        frame, issues = recalculate_lead_time(prepared(record(lead_time_days="1")))
        self.assertEqual(frame.loc[0, "calculated_lead_time_days"], 1)
        self.assertFalse(issues)
        _, issues = recalculate_lead_time(prepared(record(lead_time_days="3")))
        self.assertEqual(len(issues), 1)

    def test_booking_window_and_price_mismatch_are_flagged(self):
        frame, _ = recalculate_lead_time(prepared(record(advance_booking_window="T+7", raw_price_displayed="2000")))
        self.assertEqual(len(validate_booking_window(frame)), 1)
        self.assertEqual(len(validate_prices(frame, tolerance=0.01)), 1)

    def test_duplicate_and_outlier_detection(self):
        duplicate_frame = prepared(record(), record(observation_id=2))
        self.assertEqual(len(detect_duplicates(duplicate_frame)), 2)
        rows = [record(observation_id=n, raw_price_displayed=str(price), flight_number=f"AI{n}") for n, price in enumerate([100, 110, 105, 1000], start=1)]
        self.assertEqual(len(detect_outliers(prepared(*rows))), 1)

    def test_sold_out_rows_are_not_cleaned_price_observations(self):
        frame = prepared(record(), record(observation_id=2, scrape_status="sold_out", raw_price_displayed="1000"))
        cleaned = build_cleaned_observations(frame)
        self.assertEqual(cleaned["observation_id"].tolist(), [1])

    def test_index_table_contains_only_observed_price_rows(self):
        frame = pd.DataFrame([record(), record(observation_id=2, flight_number="AI102", scrape_status="sold_out")])
        cleaned_observations, _ = clean_raw_observations(frame)
        table = prepare_cleaned_observations_table(cleaned_observations)
        self.assertEqual(table["observation_id"].tolist(), [1])
        self.assertEqual(list(table.columns), CANONICAL_COLUMNS)
        self.assertEqual(table.loc[0, "observation_date"].isoformat(), "2026-09-20")
        self.assertEqual(table.loc[0, "flight_number"], "AI101")
        self.assertEqual(table.loc[0, "clean_base_fare"], 500)

    def test_runner_creates_cleaned_dataframe_and_quality_flags(self):
        raw_observations = pd.DataFrame([record()])
        cleaned_observations, quality_flags = clean_raw_observations(raw_observations)
        self.assertEqual(cleaned_observations["observation_id"].tolist(), [1])
        self.assertTrue(quality_flags.empty)

    def test_non_inr_currency_flagged_and_excluded(self):
        usd_record = record(observation_id=2, flight_number="AI102", currency="USD")
        raw = pd.DataFrame([record(), usd_record])
        cleaned, flags = clean_raw_observations(raw)
        self.assertEqual(cleaned["observation_id"].tolist(), [1])
        usd_flags = flags[flags["row_key"] == 2]
        self.assertFalse(usd_flags.empty)
        self.assertTrue(any("unsupported currency" in r for r in usd_flags["flag_reason"]))

    def test_duplicates_and_outliers_excluded_from_cleaned_but_flagged(self):
        # 4 distinct flights in the same group with 1 outlier fare, plus 1 duplicate of AI101
        r1 = record(observation_id=1, raw_price_displayed="1000", base_fare="500", flight_number="AI101")
        r2 = record(observation_id=2, raw_price_displayed="1050", base_fare="550", fuel_surcharge="100", flight_number="AI102")
        r3 = record(observation_id=3, raw_price_displayed="980", base_fare="480", fuel_surcharge="100", flight_number="AI103")
        r4 = record(observation_id=4, raw_price_displayed="10000", base_fare="9500", fuel_surcharge="100", flight_number="AI104") # outlier
        r5 = record(observation_id=5, raw_price_displayed="1000", base_fare="500", flight_number="AI101") # duplicate of r1
        raw = pd.DataFrame([r1, r2, r3, r4, r5])
        cleaned, flags = clean_raw_observations(raw)
        # Outlier (id 4) and duplicates (ids 1 & 5) must be excluded from cleaned observations
        self.assertNotIn(4, cleaned["observation_id"].tolist())
        self.assertNotIn(5, cleaned["observation_id"].tolist())
        self.assertNotIn(1, cleaned["observation_id"].tolist())
        self.assertIn(2, cleaned["observation_id"].tolist())
        self.assertIn(3, cleaned["observation_id"].tolist())
        # Both outlier and duplicates must be preserved in quality_flags
        flag_types = flags["flag_type"].tolist()
        self.assertIn("outlier_high", flag_types)
        self.assertIn("duplicate_suspected", flag_types)

    def test_invalid_base_fare_flagged_and_excluded(self):
        invalid_fare = record(observation_id=2, flight_number="AI102", base_fare="-100")
        raw = pd.DataFrame([record(), invalid_fare])
        cleaned, flags = clean_raw_observations(raw)
        self.assertEqual(cleaned["observation_id"].tolist(), [1])
        fare_flags = flags[flags["row_key"] == 2]
        self.assertTrue(any("base fare must be greater than zero" in r for r in fare_flags["flag_reason"]))

    def test_missing_flight_number_flagged_and_excluded(self):
        missing_fn = record(observation_id=2, flight_number="")
        raw = pd.DataFrame([record(), missing_fn])
        cleaned, flags = clean_raw_observations(raw)
        self.assertEqual(cleaned["observation_id"].tolist(), [1])
        fn_flags = flags[flags["row_key"] == 2]
        self.assertTrue(any("flight_number is missing" in r for r in fn_flags["flag_reason"]))
