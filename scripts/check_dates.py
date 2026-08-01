import duckdb
con = duckdb.connect('data/cfpb_complaints.duckdb', read_only=True)

# Check actual date format
print("=== Date received samples ===")
rows = con.execute('SELECT "Date received" FROM raw.raw_complaints WHERE "Date received" IS NOT NULL LIMIT 5').fetchall()
for r in rows:
    print(repr(r[0]))

# Check distinct date formats
print("\n=== Distinct date patterns (first char check) ===")
rows2 = con.execute("""
    SELECT SUBSTRING("Date received", 1, 10) AS sample, COUNT(*) AS cnt
    FROM raw.raw_complaints
    WHERE "Date received" IS NOT NULL
    GROUP BY sample
    ORDER BY cnt DESC
    LIMIT 10
""").fetchall()
for r in rows2:
    print(repr(r[0]), r[1])

# Try different parse formats
print("\n=== Parse test ===")
rows3 = con.execute("""
    SELECT
        COUNT(*) FILTER (WHERE TRY_STRPTIME("Date received", '%m/%d/%Y') IS NOT NULL) AS mm_dd_yyyy,
        COUNT(*) FILTER (WHERE TRY_STRPTIME("Date received", '%Y-%m-%d') IS NOT NULL) AS yyyy_mm_dd,
        COUNT(*) FILTER (WHERE TRY_CAST("Date received" AS DATE) IS NOT NULL) AS auto_cast,
        COUNT(*) AS total
    FROM raw.raw_complaints
""").fetchone()
print(f"  mm/dd/yyyy matches: {rows3[0]:,}")
print(f"  yyyy-mm-dd matches: {rows3[1]:,}")
print(f"  auto-cast matches:  {rows3[2]:,}")
print(f"  total rows:         {rows3[3]:,}")

con.close()
