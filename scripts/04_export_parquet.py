"""
04_export_parquet.py
---------------------
Exports all mart tables from DuckDB to Parquet files for Power BI consumption.

Why Parquet instead of ODBC:
  Power BI Desktop can open Parquet files natively (Get Data → Parquet) without
  any driver installation. DuckDB's Windows ODBC driver has known compatibility
  issues with Power BI Desktop. Parquet is the more reliable, zero-friction path
  for local portfolio projects.

Usage:
    python scripts/04_export_parquet.py

Output:
    data/exports/fact_complaints.parquet
    data/exports/dim_company.parquet
    data/exports/dim_product.parquet
    data/exports/dim_state.parquet
    data/exports/dim_date.parquet
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
EXPORT_DIR = Path("data/exports")

# (schema, table) tuples in dependency order
MART_TABLES = [
    ("main_marts", "dim_date"),
    ("main_marts", "dim_company"),
    ("main_marts", "dim_product"),
    ("main_marts", "dim_state"),
    ("main_marts", "fact_complaints"),
]


def main():
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found. Run dbt build first.")
        sys.exit(1)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH), read_only=True)

    print(f"[export] Writing Parquet files to {EXPORT_DIR}/")
    print("-" * 60)

    for schema, table in MART_TABLES:
        out_path = EXPORT_DIR / f"{table}.parquet"
        t0 = time.time()
        con.execute(f"""
            COPY (SELECT * FROM {schema}.{table})
            TO '{out_path.as_posix()}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
        elapsed = time.time() - t0
        size_mb = out_path.stat().st_size / 1_048_576
        row_count = con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
        print(f"  {table:<25s}  {row_count:>12,} rows  {size_mb:>7.2f} MB  ({elapsed:.1f}s)")

    con.close()
    print("-" * 60)
    print("[done] All mart tables exported.")
    print()
    print("Power BI connection instructions:")
    print("  1. Open Power BI Desktop")
    print("  2. Home → Get Data → Parquet")
    print(f"  3. Navigate to: {EXPORT_DIR.resolve()}")
    print("  4. Load each .parquet file as a separate table")
    print("  5. Create relationships in the Model view matching the FK schema")


if __name__ == "__main__":
    main()
