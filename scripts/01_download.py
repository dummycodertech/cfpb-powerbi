"""
01_download.py
--------------
Downloads the CFPB Consumer Complaint Database bulk CSV and records the snapshot date.

Usage:
    python scripts/01_download.py

Output:
    data/raw/complaints.csv
    data/raw/snapshot_date.txt
"""

import os
import sys
import urllib.request
import zipfile
import datetime
from pathlib import Path

RAW_DIR = Path("data/raw")
ZIP_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
ZIP_PATH = RAW_DIR / "complaints.csv.zip"
CSV_PATH = RAW_DIR / "complaints.csv"
SNAPSHOT_FILE = RAW_DIR / "snapshot_date.txt"


def report_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(downloaded / total_size * 100, 100)
        mb = downloaded / 1_048_576
        total_mb = total_size / 1_048_576
        print(f"\r  {pct:.1f}%  {mb:.1f} / {total_mb:.1f} MB", end="", flush=True)
    else:
        mb = downloaded / 1_048_576
        print(f"\r  {mb:.1f} MB downloaded", end="", flush=True)


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if CSV_PATH.exists():
        print(f"[skip] {CSV_PATH} already exists. Delete it to re-download.")
        return

    print(f"[download] {ZIP_URL}")
    print("  This file is ~330 MB. Estimated time: 5-15 min on a typical home connection.")
    urllib.request.urlretrieve(ZIP_URL, ZIP_PATH, reporthook=report_progress)
    print()  # newline after progress bar

    print(f"[unzip] {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        members = zf.namelist()
        print(f"  Archive contains: {members}")
        # Extract the CSV — the archive always contains exactly one CSV
        csv_members = [m for m in members if m.lower().endswith(".csv")]
        if not csv_members:
            raise RuntimeError(f"No CSV found in zip archive. Members: {members}")
        zf.extract(csv_members[0], RAW_DIR)
        extracted = RAW_DIR / csv_members[0]
        if extracted != CSV_PATH:
            extracted.rename(CSV_PATH)

    snapshot_date = datetime.date.today().isoformat()
    SNAPSHOT_FILE.write_text(f"{snapshot_date}\n")
    print(f"[snapshot] Date recorded: {snapshot_date}")

    # Clean up zip to save disk space
    ZIP_PATH.unlink()
    print(f"[done] complaints.csv ready at {CSV_PATH}")


if __name__ == "__main__":
    main()
