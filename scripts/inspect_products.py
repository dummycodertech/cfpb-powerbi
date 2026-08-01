"""
inspect_products.py
--------------------
Queries the raw DuckDB table to show all distinct Product values and their counts.
Run this AFTER 02_ingest.py to get the real product label variants before
hardcoding the standardization mapping in int_complaints_cleaned.sql.

Usage:
    python scripts/inspect_products.py
"""

import sys
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

DB_PATH = Path("data/cfpb_complaints.duckdb")


def main():
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found. Run scripts/02_ingest.py first.")
        sys.exit(1)

    con = duckdb.connect(str(DB_PATH), read_only=True)

    print("=" * 70)
    print("DISTINCT PRODUCT VALUES (raw)")
    print("=" * 70)
    rows = con.execute("""
        SELECT
            TRIM("Product")   AS product,
            COUNT(*)          AS complaint_count
        FROM raw.raw_complaints
        GROUP BY TRIM("Product")
        ORDER BY complaint_count DESC
    """).fetchall()
    for product, cnt in rows:
        print(f"  {cnt:>10,}  {product!r}")

    print()
    print("=" * 70)
    print("DISTINCT SUBMITTED VIA VALUES (raw)")
    print("=" * 70)
    rows2 = con.execute("""
        SELECT
            TRIM("Submitted via") AS submitted_via,
            COUNT(*)              AS cnt
        FROM raw.raw_complaints
        GROUP BY TRIM("Submitted via")
        ORDER BY cnt DESC
    """).fetchall()
    for via, cnt in rows2:
        print(f"  {cnt:>10,}  {via!r}")

    print()
    print("=" * 70)
    print("DISTINCT TIMELY RESPONSE VALUES (raw)")
    print("=" * 70)
    rows3 = con.execute("""
        SELECT
            TRIM("Timely response?") AS timely,
            COUNT(*)                 AS cnt
        FROM raw.raw_complaints
        GROUP BY TRIM("Timely response?")
        ORDER BY cnt DESC
    """).fetchall()
    for val, cnt in rows3:
        print(f"  {cnt:>10,}  {val!r}")

    print()
    print("=" * 70)
    print("TOTAL ROW COUNT")
    print("=" * 70)
    total = con.execute("SELECT COUNT(*) FROM raw.raw_complaints").fetchone()[0]
    print(f"  {total:,} rows")

    print()
    print("=" * 70)
    print("DATE RANGE")
    print("=" * 70)
    dates = con.execute("""
        SELECT
            MIN(TRY_STRPTIME(TRIM("Date received"), '%m/%d/%Y')) AS min_date,
            MAX(TRY_STRPTIME(TRIM("Date received"), '%m/%d/%Y')) AS max_date
        FROM raw.raw_complaints
    """).fetchone()
    print(f"  min date_received: {dates[0]}")
    print(f"  max date_received: {dates[1]}")

    con.close()


if __name__ == "__main__":
    main()
