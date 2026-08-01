# setup.ps1
# One-shot reproducible setup from a clean clone.
# Run from the project root:  .\setup.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===== CFPB Complaints Analytics Warehouse — Setup =====" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Python virtual environment ───────────────────────────────────
if (-Not (Test-Path ".venv")) {
    Write-Host "[1/5] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "[1/5] Virtual environment already exists — skipping." -ForegroundColor Green
}

# ── Step 2: Install dependencies ─────────────────────────────────────────
Write-Host "[2/5] Installing dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\pip install -r requirements.txt --quiet

# ── Step 3: Download CFPB CSV ─────────────────────────────────────────────
Write-Host "[3/5] Downloading CFPB Consumer Complaints CSV (~330 MB)..." -ForegroundColor Yellow
.\.venv\Scripts\python scripts\01_download.py

# ── Step 4: Ingest into DuckDB ────────────────────────────────────────────
Write-Host "[4/5] Ingesting CSV into DuckDB raw schema..." -ForegroundColor Yellow
.\.venv\Scripts\python scripts\02_ingest.py

# ── Step 5: Run dbt seed + build ─────────────────────────────────────────
Write-Host "[5/5] Running dbt seed + build (transforms + tests)..." -ForegroundColor Yellow
.\.venv\Scripts\dbt seed --profiles-dir .
.\.venv\Scripts\dbt build --profiles-dir .

Write-Host ""
Write-Host "===== Setup complete! =====" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  dbt docs generate + serve:"
Write-Host "    .\.venv\Scripts\dbt docs generate --profiles-dir ."
Write-Host "    .\.venv\Scripts\dbt docs serve --profiles-dir ."
Write-Host ""
Write-Host "  Export to Parquet for Power BI:"
Write-Host "    .\.venv\Scripts\python scripts\04_export_parquet.py"
Write-Host ""
Write-Host "  Run data quality verification (test-break):"
Write-Host "    .\.venv\Scripts\python scripts\03_inject_test_break.py"
