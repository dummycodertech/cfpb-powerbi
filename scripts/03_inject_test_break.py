"""
03_inject_test_break.py
-----------------------
Data quality verification script.

Workflow:
  1. Inject a deliberate duplicate row into raw.raw_complaints
  2. Run `dbt build --select stg_complaints` and confirm the unique test FAILS
  3. Remove the injected row
  4. Run `dbt build` and confirm it PASSES clean
  5. Write a log of the results to docs/test_verification.txt

Purpose: Demonstrates that the dbt unique test actually detects duplicate
complaint_ids — the single most defensible data quality claim in an interview.

Usage:
    python scripts/03_inject_test_break.py
"""

import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows (avoids CP1252 UnicodeEncodeError)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

DB_PATH = Path("data/cfpb_complaints.duckdb")
LOG_PATH = Path("docs/test_verification.txt")
VENV_DBT = Path(".venv/Scripts/dbt.exe")

# The complaint_id we will duplicate — pick the first one in the table
INJECTION_MARKER = "__INJECTED_DUPLICATE__"


def run_dbt(args: list[str]) -> tuple[int, str, str]:
    """Run a dbt command and return (returncode, stdout, stderr)."""
    cmd = [str(VENV_DBT)] + args + ["--profiles-dir", "."]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def get_first_complaint_id(con) -> str:
    row = con.execute(
        "SELECT \"Complaint ID\" FROM raw.raw_complaints LIMIT 1"
    ).fetchone()
    if not row:
        raise RuntimeError("raw.raw_complaints is empty — run 02_ingest.py first")
    return row[0]


def main():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found. Run 02_ingest.py and dbt build first.")
        sys.exit(1)

    log_lines = []

    def log(msg: str):
        print(msg)
        log_lines.append(msg)

    log("=" * 70)
    log("DATA QUALITY VERIFICATION — dbt unique test injection")
    log(f"Run timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    log("=" * 70)

    # ── Step 1: Find a complaint_id to duplicate ──────────────────────────
    con = duckdb.connect(str(DB_PATH))
    target_id = get_first_complaint_id(con)
    log(f"\n[1] Injecting duplicate: Complaint ID = {target_id!r}")

    # Insert an exact copy of that row into raw.raw_complaints
    con.execute(f"""
        INSERT INTO raw.raw_complaints
        SELECT *
        FROM raw.raw_complaints
        WHERE "Complaint ID" = '{target_id}'
        LIMIT 1
    """)
    total_before = con.execute("SELECT COUNT(*) FROM raw.raw_complaints").fetchone()[0]
    dup_count = con.execute(
        f"SELECT COUNT(*) FROM raw.raw_complaints WHERE \"Complaint ID\" = '{target_id}'"
    ).fetchone()[0]
    log(f"   Table now has {total_before:,} rows; Complaint ID {target_id!r} appears {dup_count}x")
    con.close()

    # ── Step 2: Run dbt build on stg_complaints — expect FAILURE ─────────
    log("\n[2] Running: dbt build --select stg_complaints  (expect unique test FAILURE)")
    rc, stdout, stderr = run_dbt(["build", "--select", "stg_complaints"])
    log(f"   Return code: {rc}  ({'FAILED as expected [OK]' if rc != 0 else 'UNEXPECTED PASS - check injection'})")

    # Extract the relevant test failure line
    failure_lines = [l for l in stdout.splitlines() if "FAIL" in l or "unique" in l.lower()]
    if failure_lines:
        log("   Relevant output lines:")
        for line in failure_lines[:10]:
            log(f"     {line.strip()}")
    else:
        log("   (No FAIL lines found in stdout — see full output below)")
        log("   STDOUT:")
        for line in stdout.splitlines()[-30:]:
            log(f"     {line}")

    assert rc != 0, "CRITICAL: dbt build should have FAILED with the injected duplicate but returned 0"

    # ── Step 3: Remove the injected duplicate ─────────────────────────────
    log(f"\n[3] Removing injected duplicate for Complaint ID = {target_id!r}")
    con = duckdb.connect(str(DB_PATH))

    # DuckDB doesn't support DELETE with LIMIT directly, so use ROWID approach
    # We'll use a CTE with ROW_NUMBER to identify and delete just one copy
    con.execute(f"""
        DELETE FROM raw.raw_complaints
        WHERE rowid IN (
            SELECT rowid
            FROM raw.raw_complaints
            WHERE "Complaint ID" = '{target_id}'
            ORDER BY rowid DESC
            LIMIT 1
        )
    """)
    post_count = con.execute(
        f"SELECT COUNT(*) FROM raw.raw_complaints WHERE \"Complaint ID\" = '{target_id}'"
    ).fetchone()[0]
    total_after = con.execute("SELECT COUNT(*) FROM raw.raw_complaints").fetchone()[0]
    log(f"   After removal: {total_after:,} rows; Complaint ID {target_id!r} appears {post_count}x (should be 1)")
    con.close()

    assert post_count == 1, f"Expected 1 row for {target_id} after removal, got {post_count}"

    # ── Step 4: Full dbt build — expect PASS ──────────────────────────────
    log("\n[4] Running: dbt build  (full pipeline — expect clean PASS)")
    rc2, stdout2, stderr2 = run_dbt(["build"])
    log(f"   Return code: {rc2}  ({'PASSED clean [OK]' if rc2 == 0 else 'UNEXPECTED FAILURE'})")

    pass_lines = [l for l in stdout2.splitlines() if "Completed" in l or "PASS" in l or "WARN" in l or "ERROR" in l]
    for line in pass_lines[-15:]:
        log(f"   {line.strip()}")

    assert rc2 == 0, "CRITICAL: dbt build should have PASSED after removing the duplicate"

    # ── Summary ────────────────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("VERIFICATION SUMMARY")
    log("=" * 70)
    log("[OK] Step 1: Injected a duplicate complaint_id into raw.raw_complaints")
    log("[OK] Step 2: dbt build on stg_complaints FAILED -- unique test detected the duplicate")
    log("[OK] Step 3: Removed the injected duplicate row")
    log("[OK] Step 4: Full dbt build PASSED clean after removal")
    log("\nConclusion: The dbt unique test on stg_complaints.complaint_id")
    log("correctly catches duplicate primary keys at the staging layer,")
    log("before any data propagates to the mart layer.")

    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n[log saved] {LOG_PATH}")


if __name__ == "__main__":
    main()
