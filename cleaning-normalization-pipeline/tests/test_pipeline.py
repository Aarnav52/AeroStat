import math
import os
import sys
import tempfile
import pandas as pd
import unittest
from pathlib import Path

# Add jevons_engine directory to path for direct import (it is not an installable package)
_JEVONS_ENGINE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "jevons_engine"
)
sys.path.insert(0, os.path.normpath(_JEVONS_ENGINE_DIR))
from unittest.mock import MagicMock, call, patch

from airfare_cpi.pipeline import (
    build_cleaned_observations,
    detect_cross_source_mismatches,
    detect_duplicates,
    detect_outliers,
    normalize_categories,
    recalculate_lead_time,
    validate_booking_window,
    validate_prices,
    validate_types,
)
from airfare_cpi.cleaned_table import (
    AIRLINE_CODE_MAP,
    CANONICAL_COLUMNS,
    prepare_cleaned_observations_table,
)
from airfare_cpi.pipeline_runner import clean_raw_observations
from airfare_cpi.database import run_csv_pipeline


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
        self.assertEqual(str(table.loc[0, "observation_date"]), "2026-09-20")
        self.assertEqual(table.loc[0, "flight_number"], "AI101")
        self.assertEqual(table.loc[0, "clean_base_fare"], 500)
        # airline_code must be derived from airline_name
        self.assertEqual(table.loc[0, "airline_code"], "AI")

    def test_airline_code_derived_from_airline_name_not_flight_number(self):
        """airline_code must come from AIRLINE_CODE_MAP keyed on airline_name."""
        airline_inputs = {
            " Air India ": "AI",
            "indigo": "6E",
            " SPICEJET ": "SG",
            "akasa   air": "QP",
            "FLY91": "91",
            "  vistara  ": "UK",
        }
        for airline_name, expected_code in airline_inputs.items():
            r = record(airline_name=airline_name, flight_number="XX999")
            frame = pd.DataFrame([r])
            cleaned, _ = clean_raw_observations(frame)
            table = prepare_cleaned_observations_table(cleaned)
            self.assertEqual(len(table), 1, msg=f"Airline '{airline_name}' was lost")
            self.assertEqual(table.loc[table.index[0], "airline_code"], expected_code)

    def test_unknown_airline_name_excluded_from_canonical_table(self):
        """Rows with an airline_name not in AIRLINE_CODE_MAP are excluded."""
        r = record(airline_name="UnknownAir XYZ")
        frame = pd.DataFrame([r])
        cleaned, _ = clean_raw_observations(frame)
        if cleaned.empty:
            return  # Already filtered earlier — acceptable
        table = prepare_cleaned_observations_table(cleaned)
        self.assertTrue(table.empty, "Rows with unknown airline should be excluded")

    def test_runner_creates_cleaned_dataframe_and_quality_flags(self):
        raw_observations = pd.DataFrame([record()])
        cleaned_observations, quality_flags = clean_raw_observations(raw_observations)
        self.assertEqual(cleaned_observations["observation_id"].tolist(), [1])
        self.assertTrue(quality_flags.empty)

    def test_csv_pipeline_refreshes_cleaned_table_after_ingestion(self):
        database_engine = MagicMock()
        cleaning_result = {"cleaned_rows": 1, "person_b_rows": 1}
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "observations.csv"
            pd.DataFrame([record()]).to_csv(csv_path, index=False)
            with patch("airfare_cpi.database._insert_raw", return_value={1: 1}), \
                 patch("airfare_cpi.database._insert_structured", return_value={1: 1}), \
                 patch("airfare_cpi.database._insert_flags", return_value=0), \
                 patch("airfare_cpi.pipeline_runner.run_cleaning_pipeline", return_value=cleaning_result) as run_cleaning:
                result = run_csv_pipeline(csv_path, database_engine)

        run_cleaning.assert_called_once_with(database_engine)
        self.assertEqual(result["person_b_rows"], 1)

    def test_invalid_timestamp_is_flagged_without_creating_observation_date(self):
        raw = pd.DataFrame([record(scrape_timestamp="not-a-timestamp")])
        cleaned, flags = clean_raw_observations(raw)
        self.assertTrue(cleaned.empty)
        timestamp_flags = flags[flags["row_key"] == 1]
        self.assertTrue(any("scrape_timestamp" in reason for reason in timestamp_flags["flag_reason"]))

    def test_cross_source_mismatch_is_flagged_and_retained(self):
        rows = prepared(
            record(source_id="1", raw_price_displayed="1000"),
            record(observation_id=2, source_id="2", raw_price_displayed="3000"),
        )
        issues = detect_cross_source_mismatches(rows, relative_threshold=0.35)
        self.assertEqual({issue.row_key for issue in issues}, {1, 2})
        flags = pd.DataFrame([{
            "row_key": issue.row_key,
            "flag_type": issue.flag_type,
        } for issue in issues])
        cleaned = build_cleaned_observations(rows, quality_flags=flags)
        self.assertEqual(set(cleaned["observation_id"]), {1, 2})

    def test_non_inr_currency_flagged_and_excluded(self):
        usd_record = record(observation_id=2, flight_number="AI102", currency="USD")
        raw = pd.DataFrame([record(), usd_record])
        cleaned, flags = clean_raw_observations(raw)
        self.assertEqual(cleaned["observation_id"].tolist(), [1])
        usd_flags = flags[flags["row_key"] == 2]
        self.assertFalse(usd_flags.empty)
        self.assertTrue(any("unsupported currency" in r for r in usd_flags["flag_reason"]))

    def test_duplicates_excluded_but_outliers_retained_and_flagged(self):
        r1 = record(observation_id=1, raw_price_displayed="1000", base_fare="500", flight_number="AI101")
        r2 = record(observation_id=2, raw_price_displayed="1050", base_fare="550", fuel_surcharge="100", flight_number="AI102")
        r3 = record(observation_id=3, raw_price_displayed="980", base_fare="480", fuel_surcharge="100", flight_number="AI103")
        r4 = record(observation_id=4, raw_price_displayed="10000", base_fare="9500", fuel_surcharge="100", flight_number="AI104")  # outlier
        r5 = record(observation_id=5, raw_price_displayed="1000", base_fare="500", flight_number="AI101")  # duplicate of r1
        raw = pd.DataFrame([r1, r2, r3, r4, r5])
        cleaned, flags = clean_raw_observations(raw)
        self.assertIn(4, cleaned["observation_id"].tolist())
        self.assertNotIn(5, cleaned["observation_id"].tolist())
        self.assertNotIn(1, cleaned["observation_id"].tolist())
        self.assertIn(2, cleaned["observation_id"].tolist())
        self.assertIn(3, cleaned["observation_id"].tolist())
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


# ---------------------------------------------------------------------------
# Jevons engine unit tests (no Supabase dependency)
# ---------------------------------------------------------------------------

class JevonsCalculationTests(unittest.TestCase):
    """Pure-Python tests for the Jevons calculation logic.
    These tests do NOT require a Supabase connection.
    """

    def _make_df(self, rows):
        """Build a minimal cleaned_observations_table DataFrame for Jevons tests."""
        return pd.DataFrame(rows)

    def _base_row(self, obs_date, route_id, airline_code, cabin, window, fare):
        return {
            "observation_date": obs_date,
            "route_id": route_id,
            "airline_code": airline_code,
            "cabin_class": cabin,
            "advance_booking_window": window,
            "clean_base_fare": fare,
            "data_provenance": "synthetic",
        }

    def test_deterministic_jevons_known_prices(self):
        """
        Given:
          base  = [100, 200]   (two product grains, same route/window)
          current = [110, 220]
          price_relatives = [1.10, 1.10]
          geometric mean of log-relatives = log(1.10)
          elementary Jevons = exp(log(1.10)) * 100 = 110.0
        """
        from jevons_engine_cloud import compute_apix_jevons_index  # type: ignore

        # Two product grains: (route 1, AI, economy, T+1) and (route 1, 6E, economy, T+1)
        rows = [
            self._base_row("2026-01-01", 1, "AI", "economy", "T+1", 100.0),
            self._base_row("2026-01-01", 1, "6E", "economy", "T+1", 200.0),
            self._base_row("2026-02-01", 1, "AI", "economy", "T+1", 110.0),
            self._base_row("2026-02-01", 1, "6E", "economy", "T+1", 220.0),
        ]
        df = self._make_df(rows)
        payload = compute_apix_jevons_index(df)

        elementary = [p for p in payload if p["index_type"] == "elementary"]
        self.assertEqual(len(elementary), 1)
        self.assertAlmostEqual(elementary[0]["index_value"], 110.0, places=2)

        route = [p for p in payload if p["index_type"] == "route"]
        self.assertEqual(len(route), 1)
        self.assertAlmostEqual(route[0]["index_value"], 110.0, places=2)

        national = [p for p in payload if p["index_type"] == "national"]
        self.assertEqual(len(national), 1)
        self.assertAlmostEqual(national[0]["index_value"], 110.0, places=2)

    def test_no_fan_out_with_multiple_observations_per_grain(self):
        """
        Two base observations and two current observations for the SAME grain
        must NOT produce a 2×2=4 merged row fan-out.
        The pre-merge aggregation must collapse each side to 1 row.
        The elementary Jevons value must equal the ratio of geometric means.
        num_observations_used must reflect the total collapsed count.
        """
        from jevons_engine_cloud import compute_apix_jevons_index  # type: ignore

        rows = [
            # 2 base observations for the same grain (different scrapes / sources)
            self._base_row("2026-01-01", 1, "AI", "economy", "T+1", 100.0),
            self._base_row("2026-01-01", 1, "AI", "economy", "T+1", 120.0),
            # 2 current observations for the same grain
            self._base_row("2026-02-01", 1, "AI", "economy", "T+1", 110.0),
            self._base_row("2026-02-01", 1, "AI", "economy", "T+1", 132.0),
        ]
        df = self._make_df(rows)
        payload = compute_apix_jevons_index(df)

        elementary = [p for p in payload if p["index_type"] == "elementary"]
        self.assertEqual(len(elementary), 1, "Fan-out detected: expected exactly 1 elementary row")

        # geometric mean base = sqrt(100 * 120) = 109.544...
        # geometric mean curr = sqrt(110 * 132) = 120.499...
        # expected index = (120.499 / 109.544) * 100 = 109.999... ≈ 110.0
        geo_base = math.exp((math.log(100) + math.log(120)) / 2)
        geo_curr = math.exp((math.log(110) + math.log(132)) / 2)
        expected_index = (geo_curr / geo_base) * 100
        self.assertAlmostEqual(elementary[0]["index_value"], expected_index, places=2)

        # num_observations_used = 2 (base) + 2 (current) = 4
        self.assertEqual(elementary[0]["num_observations_used"], 4)

    def test_provenance_mix_splits_categories_at_all_rollup_levels(self):
        from jevons_engine_cloud import compute_apix_jevons_index  # type: ignore

        rows = [
            self._base_row("2026-01-01", 1, "AI", "economy", "T+1", 100.0),
            self._base_row("2026-02-01", 1, "AI", "economy", "T+1", 110.0),
            self._base_row("2026-01-01", 1, "6E", "economy", "T+7", 200.0),
            self._base_row("2026-02-01", 1, "6E", "economy", "T+7", 220.0),
        ]
        rows[0]["data_provenance"] = "real_scraped|synthetic"
        rows[1]["data_provenance"] = "synthetic"
        rows[2]["data_provenance"] = "kaggle_seeded"
        rows[3]["data_provenance"] = "real_scraped|kaggle_seeded"

        payload = compute_apix_jevons_index(self._make_df(rows))
        for index_type in ("elementary", "route", "national"):
            mixes = [row["data_provenance_mix"] for row in payload if row["index_type"] == index_type]
            self.assertTrue(mixes)
            for mix in mixes:
                self.assertNotIn("real_scraped|synthetic", mix["data_sources"])
                self.assertNotIn("real_scraped|kaggle_seeded", mix["data_sources"])
        route_mix = next(row["data_provenance_mix"] for row in payload if row["index_type"] == "route")
        self.assertEqual(
            set(route_mix["data_sources"]),
            {"real_scraped", "synthetic", "kaggle_seeded"},
        )

    def test_route_and_window_normalization_prevents_split_weights(self):
        """Mixed route ID and booking window text should normalize to the same analytic grain."""
        from jevons_engine_cloud import compute_apix_jevons_index  # type: ignore

        rows = [
            self._base_row("2026-01-01", "1", "AI", "economy", "t+1", 100.0),
            self._base_row("2026-01-01", 1, "6E", "economy", "T+7", 200.0),
            self._base_row("2026-02-01", "1.0", "AI", "economy", "T+1", 110.0),
            self._base_row("2026-02-01", 1, "6E", "economy", "t+7", 220.0),
        ]

        payload = compute_apix_jevons_index(self._make_df(rows))

        elementary = [p for p in payload if p["index_type"] == "elementary"]
        self.assertEqual(len(elementary), 2)
        self.assertEqual({p["route_id"] for p in elementary}, {"1", "1"})
        self.assertEqual({p["advance_booking_window"] for p in elementary}, {"T+1", "T+7"})

        route = [p for p in payload if p["index_type"] == "route"]
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0]["route_id"], "1")

    def test_payload_schema_keys_match_sql_schema(self):
        """All payload dicts must contain exactly the expected schema keys."""
        from jevons_engine_cloud import compute_apix_jevons_index  # type: ignore

        rows = [
            self._base_row("2026-01-01", 1, "AI", "economy", "T+1", 100.0),
            self._base_row("2026-02-01", 1, "AI", "economy", "T+1", 110.0),
        ]
        payload = compute_apix_jevons_index(self._make_df(rows))
        expected_keys = {
            "observation_date", "base_period_date", "index_type",
            "route_id", "advance_booking_window", "index_value",
            "num_observations_used", "data_provenance_mix",
        }
        forbidden_keys = {"index_date", "created_at"}
        for row in payload:
            self.assertTrue(
                expected_keys.issubset(row.keys()),
                f"Missing schema keys in payload row: {expected_keys - row.keys()}"
            )
            for bad_key in forbidden_keys:
                self.assertNotIn(bad_key, row, f"Forbidden key '{bad_key}' found in payload")

    def test_index_type_values_match_check_constraint(self):
        """index_type must be exactly 'elementary', 'route', or 'national'."""
        from jevons_engine_cloud import compute_apix_jevons_index  # type: ignore

        rows = [
            self._base_row("2026-01-01", 1, "AI", "economy", "T+1", 100.0),
            self._base_row("2026-02-01", 1, "AI", "economy", "T+1", 110.0),
        ]
        payload = compute_apix_jevons_index(self._make_df(rows))
        allowed = {"elementary", "route", "national"}
        for row in payload:
            self.assertIn(
                row["index_type"], allowed,
                f"Invalid index_type: '{row['index_type']}'"
            )

    def test_idempotency_delete_called_once_before_insert(self):
        """
        push_to_supabase must delete existing rows for affected dates ONCE,
        before any inserts — not between insert batches.
        """
        from jevons_engine_cloud import push_to_supabase  # type: ignore

        payload = [
            {
                "observation_date": "2026-02-01",
                "base_period_date": "2026-01-01",
                "index_type": "national",
                "route_id": None,
                "advance_booking_window": None,
                "index_value": 110.0,
                "num_observations_used": 2,
                "data_provenance_mix": {},
            }
        ]

        # Mock Supabase client
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_delete_chain = MagicMock()
        mock_table.delete.return_value = mock_delete_chain
        mock_delete_chain.eq.return_value = mock_delete_chain
        mock_delete_chain.execute.return_value = MagicMock()
        mock_insert_chain = MagicMock()
        mock_table.insert.return_value = mock_insert_chain
        mock_insert_chain.execute.return_value = MagicMock(data=[{}])

        push_to_supabase(mock_client, payload, table_name="index_values")

        # Delete must be called exactly once (one date in payload)
        mock_delete_chain.eq.assert_called_once_with("observation_date", "2026-02-01")
        mock_delete_chain.execute.assert_called_once()

        # Insert must be called exactly once (one batch)
        mock_table.insert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
