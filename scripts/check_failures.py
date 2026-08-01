import duckdb
con = duckdb.connect('data/cfpb_complaints.duckdb', read_only=True)

# Which rows have NULL date after TRY_CAST?
print("=== Rows with NULL date_received after cast ===")
rows = con.execute("""
    SELECT
        TRIM("Complaint ID") AS complaint_id,
        "Date received",
        "Product",
        LEFT("Issue", 60) AS issue_preview
    FROM raw.raw_complaints
    WHERE TRY_CAST(TRIM("Date received") AS DATE) IS NULL
    LIMIT 20
""").fetchall()
for r in rows:
    print(r)

print(f"\nTotal null-date rows: {len(rows)}")

# Check if these same complaint_ids are the duplicates
print("\n=== Are these the duplicate complaint_ids? ===")
rows2 = con.execute("""
    SELECT TRIM("Complaint ID") AS cid, COUNT(*) AS cnt
    FROM raw.raw_complaints
    GROUP BY TRIM("Complaint ID")
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    LIMIT 20
""").fetchall()
for r in rows2:
    print(r)
print(f"Total complaint_ids with duplicates: {len(rows2)}")

con.close()
