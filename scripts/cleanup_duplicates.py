import duckdb

con = duckdb.connect('data/cfpb_complaints.duckdb')

# Check current count
before = con.execute(
    "SELECT COUNT(*) FROM raw.raw_complaints WHERE \"Complaint ID\" = '8489941'"
).fetchone()[0]
total_before = con.execute("SELECT COUNT(*) FROM raw.raw_complaints").fetchone()[0]
print(f"Before: complaint 8489941 appears {before}x, total rows = {total_before:,}")

# Delete all but the FIRST copy (lowest rowid)
con.execute("""
    DELETE FROM raw.raw_complaints
    WHERE rowid IN (
        SELECT rowid FROM raw.raw_complaints
        WHERE "Complaint ID" = '8489941'
        ORDER BY rowid DESC
        LIMIT 2
    )
""")

after = con.execute(
    "SELECT COUNT(*) FROM raw.raw_complaints WHERE \"Complaint ID\" = '8489941'"
).fetchone()[0]
total_after = con.execute("SELECT COUNT(*) FROM raw.raw_complaints").fetchone()[0]
print(f"After: complaint 8489941 appears {after}x, total rows = {total_after:,}")

con.close()
print("Cleanup done.")
