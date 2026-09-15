import argparse
import site
from pathlib import Path

site.addsitedir(str(Path(__file__).parent / ".dist"))

from airfare_cpi.database import apply_migration, engine, run_csv_pipeline
from airfare_cpi.pipeline_runner import run_cleaning_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the Airfare CPI MVP CSV pipeline.")
    parser.add_argument("--migrate", action="store_true", help="Apply the MVP raw/cleaned schema migration.")
    parser.add_argument("--csv", type=Path, help="CSV observation file to ingest.")
    parser.add_argument("--run-cleaning", action="store_true", help="Read raw observations and refresh Person B's table.")
    args = parser.parse_args()
    db_engine = engine()
    if args.migrate:
        for migration_path in sorted(Path("migrations").glob("*.sql")):
            with db_engine.begin() as connection:
                apply_migration(connection, migration_path)
    if args.csv:
        summary = run_csv_pipeline(args.csv, db_engine)
        print({key: value for key, value in summary.items() if key != "profile"})
    if args.run_cleaning:
        summary = run_cleaning_pipeline(db_engine)
        print({key: value for key, value in summary.items() if key != "profile"})
    if not args.migrate and not args.csv and not args.run_cleaning:
        parser.print_help()


if __name__ == "__main__":
    main()
