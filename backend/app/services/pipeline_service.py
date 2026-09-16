import logging
import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

# Add cleaning pipeline and jevons engine to python path if not present
REPO_ROOT = Path(__file__).resolve().parents[3]
CLEANING_PATH = REPO_ROOT / "cleaning-normalization-pipeline"
JEVONS_PATH = REPO_ROOT / "jevons_engine"

if str(CLEANING_PATH) not in sys.path:
    sys.path.insert(0, str(CLEANING_PATH))
if str(JEVONS_PATH) not in sys.path:
    sys.path.insert(0, str(JEVONS_PATH))

from airfare_cpi.pipeline_runner import clean_raw_observations
from airfare_cpi.cleaned_table import prepare_cleaned_observations_table, write_cleaned_observations_table
from jevons_engine_cloud import compute_apix_jevons_index, _load_dgca_route_weights, push_to_supabase

logger = logging.getLogger(__name__)

class PipelineService:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL", "").strip()

    def get_sqlalchemy_engine(self):
        if not self.db_url:
            raise ValueError("DATABASE_URL is not set.")
        sa_url = self.db_url
        if sa_url.startswith("postgresql://"):
            sa_url = sa_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return create_engine(sa_url)

    def run_full_pipeline(self) -> dict:
        """
        Runs the end-to-end cleaning and Jevons index calculation pipeline:
        1. Reads raw flight observations from flight_observations table.
        2. Cleans & normalizes fares via cleaning pipeline.
        3. Updates cleaned_observations_table.
        4. Calculates Elementary, Route-level, and National Jevons indices (DGCA & booking-window weighted).
        5. Stores the calculated index values into index_values table.
        """
        logger.info("Starting automated cleaning and Jevons calculation pipeline...")
        engine = self.get_sqlalchemy_engine()

        # Step 1: Read all observed flights
        query = "SELECT * FROM flight_observations WHERE scrape_status = 'observed' AND raw_price_displayed IS NOT NULL"
        raw_df = pd.read_sql(query, engine)
        logger.info(f"Loaded {len(raw_df)} observed flights from database.")

        if raw_df.empty:
            return {
                "status": "warning",
                "message": "No observed flights found in database.",
                "raw_count": 0,
                "cleaned_count": 0,
                "index_records": 0,
            }

        # Step 2: Clean and normalize observations
        cleaned_df, quality_flags = clean_raw_observations(raw_df)
        person_b_table = prepare_cleaned_observations_table(cleaned_df)
        logger.info(f"Cleaned {len(cleaned_df)} rows, generated {len(person_b_table)} canonical records.")

        # Step 3: Write cleaned observations table
        written_cleaned = write_cleaned_observations_table(person_b_table, engine)
        logger.info(f"Successfully refreshed cleaned_observations_table with {written_cleaned} records.")

        # Step 4: Load DGCA route weights and calculate Jevons Index
        dgca_weights = _load_dgca_route_weights()
        payload = compute_apix_jevons_index(person_b_table, dgca_route_weights=dgca_weights, include_base_date=True)
        logger.info(f"Calculated {len(payload)} Jevons index records across all hierarchy levels.")

        # Step 5: Push index values to index_values table
        inserted_indexes = push_to_supabase(payload, table_name="index_values")

        return {
            "status": "success",
            "raw_observations_read": len(raw_df),
            "cleaned_observations_written": written_cleaned,
            "index_records_generated": len(payload),
            "dates_processed": sorted(list(person_b_table["observation_date"].astype(str).unique())),
            "dgca_weights_loaded": len(dgca_weights),
        }

pipeline_service = PipelineService()
