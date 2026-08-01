"""
02_ingest.py
------------
Loads the raw complaints CSV into DuckDB as raw.raw_complaints.
All columns are stored as VARCHAR — no casting, no renaming, no business logic.
This is the source of truth; downstream dbt models handle transformation.

Usage:
    python scripts/02_ingest.py

Output:
    data/cfpb_complaints.duckdb  (schema: raw, table: raw_complaints)
"""

import sys
import time
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

DB_PATH = Path("data/cfpb_complaints.duckdb")
CSV_PATH = Path("data/raw/complaints.csv")


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run scripts/01_download.py first.")
        sys.exit(1)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"[connect] Opening DuckDB at {DB_PATH}")
    con = duckdb.connect(str(DB_PATH))

    print("[schema] Creating raw schema if not exists")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    print(f"[load] Reading {CSV_PATH} into raw.raw_complaints ...")
    print("  (This may take 1-3 minutes for ~7M rows)")
    t0 = time.time()

    con.execute("""
        CREATE OR REPLACE TABLE raw.raw_complaints AS
        SELECT *
        FROM read_csv(
            'data/raw/complaints.csv',
            header = true,
            all_varchar = true,
            ignore_errors = true,
            quote = '"',
            escape = '"'
        )
    """)

    elapsed = time.time() - t0

    row_count = con.execute("SELECT COUNT(*) FROM raw.raw_complaints").fetchone()[0]
    col_count = con.execute(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='raw' AND table_name='raw_complaints'"
    ).fetchone()[0]

    print(f"[done] Loaded {row_count:,} rows x {col_count} columns in {elapsed:.1f}s")
    print(f"[columns] Schema preview:")
    cols = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='raw' AND table_name='raw_complaints' ORDER BY ordinal_position"
    ).fetchall()
    for name, dtype in cols:
        print(f"  {name!r:45s} {dtype}")

    con.close()
    print(f"\n[ready] Database: {DB_PATH}")


if __name__ == "__main__":
    main()
