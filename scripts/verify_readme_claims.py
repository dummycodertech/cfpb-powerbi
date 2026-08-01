import duckdb

con = duckdb.connect('data/cfpb_complaints.duckdb', read_only=True)

# ── 1. Verify complaint_id type in fact_complaints ────────────────────────
print("=== complaint_id column type ===")
row = con.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'main_marts'
      AND table_name   = 'fact_complaints'
      AND column_name  = 'complaint_id'
""").fetchone()
print(f"  fact_complaints.complaint_id dtype: {row}")

# ── 2. Check dim_company columns (was total_complaints dropped?) ──────────
print("\n=== dim_company columns ===")
cols = con.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'main_marts'
      AND table_name   = 'dim_company'
    ORDER BY ordinal_position
""").fetchall()
for c in cols:
    print(f"  {c[0]}")

# ── 3. Investigate the 1,310 null-ID rows ────────────────────────────────
print("\n=== Sample of rows with NULL Complaint ID (raw table) ===")
rows = con.execute("""
    SELECT
        "Date received",
        "Product",
        LEFT("Consumer complaint narrative", 80) AS narrative_preview,
        "Company",
        "State"
    FROM raw.raw_complaints
    WHERE "Complaint ID" IS NULL
    LIMIT 10
""").fetchall()
for r in rows:
    print(r)

# How many have non-null narrative?
print("\n=== Do null-ID rows have content in narrative? ===")
r2 = con.execute("""
    SELECT
        COUNT(*) AS total_null_id,
        COUNT("Consumer complaint narrative") AS has_narrative,
        COUNT("Date received") AS has_date,
        COUNT("Product") AS has_product
    FROM raw.raw_complaints
    WHERE "Complaint ID" IS NULL
""").fetchone()
print(f"  total null-ID rows:  {r2[0]:,}")
print(f"  have narrative:      {r2[1]:,}")
print(f"  have date:           {r2[2]:,}")
print(f"  have product:        {r2[3]:,}")

# ── 4. Row-count arithmetic check ────────────────────────────────────────
print("\n=== Row count reconciliation ===")
raw_total = con.execute("SELECT COUNT(*) FROM raw.raw_complaints").fetchone()[0]
fact_total = con.execute("SELECT COUNT(*) FROM main_marts.fact_complaints").fetchone()[0]
print(f"  raw.raw_complaints:         {raw_total:,}")
print(f"  main_marts.fact_complaints: {fact_total:,}")
print(f"  difference:                 {raw_total - fact_total:,}")

con.close()
