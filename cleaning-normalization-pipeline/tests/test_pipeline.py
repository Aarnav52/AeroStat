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
        frame = pd.DataFrame([record(), record(observation_id=2, scrape_status="sold_out")])
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
