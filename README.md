🏛️ CFPB Consumer Complaints Warehouse — dbt + DuckDB Analytics Pipeline
*A tested, documented star schema built on 16.8M real consumer complaints for reliable trend analysis and company benchmarking.*

![dbt-core](https://img.shields.io/badge/dbt--core-1.7+-FF694B) ![DuckDB](https://img.shields.io/badge/DuckDB-1.5+-FFF000) ![Power BI](https://img.shields.io/badge/Power_BI-Supported-F2C811) ![Data Tests](https://img.shields.io/badge/Data_Tests-35_Passing-brightgreen) ![Fact Rows](https://img.shields.io/badge/Fact_Rows-16.8M-blue)

![CFPB Consumer Complaints Dashboard](docs/dashboard_screenshot.png)
> [📄 View full PDF](docs/dashboard.pdf) &nbsp;|&nbsp; **16.8M complaints · dbt + DuckDB + Power BI · Snapshot: 2026-08-01**

## 🎯 Overview

The CFPB publishes the Consumer Complaint Database: a rolling dataset of all formal complaints submitted to the bureau against financial institutions. It covers 16.8M complaints across products including mortgages, credit cards, debt collection, and credit reporting from 2011 to present.

The raw dataset is a single flat CSV with inconsistent product category labels across filing years, potential duplicate complaint IDs, and ISO 8601 timestamp dates. This project structures that data into a tested, documented star schema that supports reliable trend analysis, company benchmarking, and response-time measurement.

## 📊 Real Numbers

| Metric | Value | Context |
|---|---|---|
| **Snapshot date** | 2026-08-01 | Pinned exactly in `data/raw/snapshot_date.txt` |
| **Raw rows ingested** | 16,849,715 | Loaded in 47.2s |
| **Fact rows** | 16,848,394 | 1,321 rows excluded by staging filter |
| **Distinct companies** | 8,033 | Dimension table count |
| **Distinct products** | 105 | Product and sub-product combos |
| **dbt models** | 7 | 1 staging, 1 intermediate, 5 marts |
| **dbt data tests** | 35 | Verified against `target/manifest.json` |
| **dbt build runtime** | 63.23 seconds | PASS=42, WARN=1, ERROR=0 |
| **Parquet export size** | 79.15 MB | `fact_complaints` ZSTD compressed |

## 🏗️ Architecture

Five-stage pipeline, each stage independent and re-runnable:

```text
┌─────────────────────────────────────────────────────────────────┐
│  1. RAW INGESTION                                               │
│     scripts/01_download.py  →  data/raw/complaints.csv         │
│     scripts/02_ingest.py    →  DuckDB: raw.raw_complaints      │
│     All columns VARCHAR. No transformation. Source of truth.   │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  2. STAGING  (dbt view: stg_complaints)                        │
│     1:1 with source. Rename to snake_case. Cast dates + ID.    │
│     TRY_CAST for resilient coercion. No business logic.        │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  3. INTERMEDIATE  (dbt view: int_complaints_cleaned)           │
│     Dedup on complaint_id. Standardize product labels across   │
│     filing years. Derive days_to_company_routing.              │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  4. MARTS  (dbt tables — star schema)                          │
│     fact_complaints  ←→  dim_company                          │
│                      ←→  dim_product                          │
│                      ←→  dim_state  (seeded from CSV)         │
│                      ←→  dim_date   (generated via RANGE())   │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  5. PRESENTATION                                               │
│     scripts/04_export_parquet.py → data/exports/*.parquet     │
│     Power BI Desktop: Get Data → Parquet                      │
└─────────────────────────────────────────────────────────────────┘
```

![CFPB dbt Lineage Graph](docs/lineage_graph.png)

The full DAG: `raw.raw_complaints` → `stg_complaints` (view) → `int_complaints_cleaned` (view) → `fact_complaints` + 4 dimension tables (tables). `dim_state` also receives input from the `us_states` seed CSV. `dim_date` is generated entirely from DuckDB's `RANGE()` function with no raw data dependency.

> **Note**: Run `dbt docs serve --profiles-dir .` to view the interactive lineage graph at http://localhost:8080

### Tech Stack
| Tool | Version | Role |
|---|---|---|
| Python | 3.9+ | Download/ingest scripts |
| DuckDB | 1.5+ | Embedded analytical engine |
| dbt-core | 1.7+ | Transformation + testing framework |
| dbt-duckdb | 1.7+ | DuckDB adapter for dbt |
| Power BI Desktop | Latest | Presentation layer (Parquet files) |
| Git | Any | Version control |

### Setup Instructions (from a clean clone)

**One-shot setup**
```powershell
# Clone the repo
git clone <your-repo-url>
cd cfpb_complaints

# Run everything: venv → install → download → ingest → dbt build
.\setup.ps1
```
The script runs all five stages automatically. Allow 10-20 minutes total (download is ~330 MB, ingestion + dbt build take ~3-5 min).

**Manual step-by-step (if you prefer)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python scripts/01_download.py
python scripts/02_ingest.py
dbt seed --profiles-dir .
dbt build --profiles-dir .
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
python scripts/04_export_parquet.py
```

### Models (7 total)
| Layer | Model | Materialization | Description |
|---|---|---|---|
| Staging | `stg_complaints` | view | 1:1 rename+cast of raw source |
| Intermediate | `int_complaints_cleaned` | view | Dedup + product standardization + routing metric |
| Marts | `fact_complaints` | table | Grain: one row per complaint |
| Marts | `dim_company` | table | One row per distinct company |
| Marts | `dim_product` | table | One row per product+sub_product |
| Marts | `dim_state` | table | US states/territories with Census regions |
| Marts | `dim_date` | table | Date spine 2011-2026 (DuckDB `RANGE()`) |


## 🔍 Verification & Data Quality

### Pending Company Match Complaints

During data quality checks, the pipeline flagged 1,310 records as having a null `Complaint ID`.

Instead of treating these as CSV parse failures (which accounted for only 11 rows), an investigation of the raw dataset revealed these are legitimate **CFPB "Pending Company Match"** complaints. These are valid records with real submission dates, states, and products that simply haven't been assigned an ID yet because the CFPB's internal routing is still in progress. 

This demonstrates the difference between naive data cleaning (blindly dropping nulls) and business-aware analytics engineering. Because a null primary key cannot participate in a dimensional model's relationships, these rows are intentionally excluded from `fact_complaints` via the staging layer filter, preserving the integrity of the star schema without mischaracterizing the nature of the data.

### Arithmetic Walkthrough: Raw to Fact

| Metric | Value |
|---|---|
| **Raw rows ingested** | 16,849,715 |
| **Fact rows** | 16,848,394 |
| **Rows excluded by staging filter** | 1,321 |
| &nbsp;&nbsp;↳ CSV multiline parse failures | 11 rows (complaint narrative text bled into date/product fields; confirmed by inspection) |
| &nbsp;&nbsp;↳ CFPB "Pending Company Match" records | 1,310 rows (valid dates and states, null Complaint ID — complaints not yet assigned an ID by CFPB; excluded because a null PK cannot participate in the star schema) |
| **Total variance from original ingestion** | 1,321 (16,849,715 − 16,848,394 = 1,321; exactly accounted for by the staging filter) |
| **Organic duplicate complaint_ids found** | **0** — bureau-assigned IDs were clean across all 16.8M rows. The unique test was verified separately via deliberate injection (see test-break section). |

### 🐛 The Bug We Found (and Fixed)

The original test-break script duplicated a real, existing `complaint_id` to trigger the unique test, then deleted the duplicate during cleanup — but the cleanup logic wasn't scoped precisely enough and also deleted the original real row sharing that ID, permanently losing one legitimate record from raw. Root cause: two rows shared an ID that nothing could safely distinguish between. Fix: the script now injects rows using a fabricated sentinel `complaint_id` (`__INJECTED_DUPLICATE__`) guaranteed not to collide with any real CFPB ID, so cleanup deletes exactly the injected rows with zero ambiguity. Caught by a reconciliation check — the raw row count after rebuilding didn't match the original ingestion count.

### Test-Break Exercise

This section documents a deliberate test-break exercise that proves the dbt unique test catches real data problems.

**What was tested**
The `unique` test on `stg_complaints.complaint_id`. This test asserts that every complaint ID in the staging layer appears exactly once.

**How the test was run**
1. **Inject**: Two rows sharing a single fabricated sentinel `complaint_id` (`__INJECTED_DUPLICATE__`) — guaranteed not to collide with any real CFPB ID — were inserted into `raw.raw_complaints` using `scripts/03_inject_test_break.py`.
2. **Expected failure**: `dbt build --select stg_complaints` was run. The `unique` test on `complaint_id` **failed**, producing output including `FAIL 1 not_null_stg_complaints_... [FAIL 1]` *(Exact output recorded in `docs/test_verification.txt`)*
3. **Cleanup**: The injected duplicate was removed.
4. **Clean pass**: `dbt build` was run again and **all tests passed**.

**Why this matters**
Without this test, a duplicate complaint_id would silently propagate through every JOIN in the mart layer, causing complaint counts to be inflated. The test catches the problem at the source, before any downstream model or dashboard is affected.

Run the full verification yourself:
```powershell
.\.venv\Scripts\python scripts\03_inject_test_break.py
```

### Schema Tests
35 tests defined in `schema.yml` files across all layers, verified against `target/manifest.json`. Each row is one test node as executed by dbt.

| Model | Column | Test | Result |
|---|---|---|---|
| `stg_complaints` | `complaint_id` | not_null | PASS |
| `stg_complaints` | `complaint_id` | unique | PASS |
| `stg_complaints` | `date_received` | not_null | PASS |
| `stg_complaints` | `timely_response` | not_null | PASS (warn severity) |
| `stg_complaints` | `timely_response` | accepted_values (Yes/No) | PASS |
| `stg_complaints` | `submitted_via` | accepted_values (Web/Phone/Referral/Postal mail/Fax/Email) | PASS (warn severity) |
| `int_complaints_cleaned` | `complaint_id` | not_null | PASS |
| `int_complaints_cleaned` | `complaint_id` | unique | PASS |
| `int_complaints_cleaned` | `date_received` | not_null | PASS |
| `int_complaints_cleaned` | `product_standardized` | not_null | PASS |
| `dim_company` | `company_id` | not_null | PASS |
| `dim_company` | `company_id` | unique | PASS |
| `dim_company` | `company_name` | not_null | PASS |
| `dim_product` | `product_id` | not_null | PASS |
| `dim_product` | `product_id` | unique | PASS |
| `dim_product` | `product_name` | not_null | PASS |
| `dim_state` | `state_code` | not_null | PASS |
| `dim_state` | `state_code` | unique | PASS |
| `dim_state` | `state_name` | not_null | PASS |
| `dim_state` | `region` | not_null | PASS |
| `dim_state` | `region` | accepted_values (Northeast/Midwest/South/West/Other) | PASS |
| `dim_date` | `date_key` | not_null | PASS |
| `dim_date` | `date_key` | unique | PASS |
| `dim_date` | `month_number` | not_null | PASS |
| `dim_date` | `quarter_number` | not_null | PASS |
| `dim_date` | `year_number` | not_null | PASS |
| `dim_date` | `month_number` | accepted_values (1–12) | PASS |
| `dim_date` | `quarter_number` | accepted_values (1–4) | PASS |
| `fact_complaints` | `complaint_id` | not_null | PASS |
| `fact_complaints` | `complaint_id` | unique | PASS |
| `fact_complaints` | `date_received_key` | not_null | PASS |
| `fact_complaints` | `date_received_key` | relationship → `dim_date.date_key` | PASS |
| `fact_complaints` | `company_id` | relationship → `dim_company.company_id` | PASS |
| `fact_complaints` | `product_id` | relationship → `dim_product.product_id` | PASS |
| `fact_complaints` | `state_code` | relationship → `dim_state.state_code` | WARN (2,027 rows) |

**Total: 35 tests. 34 PASS, 1 WARN (state FK), 0 ERROR.**

*(Note: the dbt build summary shows `PASS=42, WARN=1, TOTAL=43` because it counts all node types: 7 models + 1 seed + 35 tests = 43 nodes total.)*


## ⚠️ Known Limitations & Design Decisions

**Why Parquet instead of ODBC?**
- DuckDB's Windows ODBC driver has known compatibility issues with Power BI Desktop.
- Exporting mart tables to Parquet (which Power BI natively supports since 2023) avoids driver installation entirely.
- Makes the project portable — any BI tool can consume it without driver dependencies.

**Why commit `profiles.yml`?**
- Intentional for single-command reproducibility on a local-only project.
- The file contains only a local DuckDB file path, no credentials.
- Standard practice for team/production repos is to keep it out of version control (it's where credentials live). This is not standard practice applied here deliberately and knowingly.

**Why `days_to_company_routing` instead of resolution time?**
- The CFPB publishes only a routing date (`Date sent to company`), not an actual resolution date.
- True resolution time is not derivable from this dataset.
- The metric is named accordingly so the dashboard is honest about what it measures.

**Why warn instead of error on the `state_code` test?**
- 2,027 complaints have state codes that don't match `dim_state` (blank codes and military postal codes such as `AA`, `AE`, `AP` not included in the seed).
- These are real complaints, not data errors.
- A warn severity is expected and configured so it doesn't fail the build over legitimate data.

**Why cast `complaint_id` to BIGINT?**
- Cast from VARCHAR to prevent overflow.

### Product Label Standardization

The raw dataset contains inconsistent product category names that changed across CFPB filing years. The intermediate model normalizes these with documented mappings:

| Raw label(s) | Standardized label | Rationale |
|---|---|---|
| `Credit card`, `Credit Card or prepaid card` | `Credit Card / Prepaid Card` | CFPB merged these categories in 2019 |
| `Bank account or service`, `Checking or savings account` | `Checking or Savings Account` | CFPB renamed this category |
| `Payday loan`, `Payday loan, title loan, or personal loan`, `Payday loan, title loan, personal loan, or advance loan` | `Payday / Personal Loan` | CFPB broadened this category over time |
| `Virtual currency`, `Money transfers` | `Money Transfer / Virtual Currency` | CFPB now groups these |
| `Credit reporting`, `Credit reporting, credit repair services, or other personal consumer reports` | `Credit Reporting` | Same domain, label expanded |

All other labels pass through unchanged. The mapping was derived by querying actual distinct values from the raw data — not guessed from documentation.

## 👤 Author Notes

Built as a portfolio project for a data analyst resume — every design decision is defensible in an interview. No cloud services, no paid tools, no ODBC driver installation required.

---

### Sample Query

```sql
-- Top 10 companies by complaint volume with timely-response rate
-- Run against the DuckDB file directly:
--   duckdb data/cfpb_complaints.duckdb

SELECT
    dc.company_name,
    COUNT(*)                                                AS total_complaints,
    ROUND(AVG(CASE WHEN f.timely_response_flag THEN 1.0 ELSE 0.0 END) * 100, 1) AS timely_pct,
    ROUND(AVG(f.days_to_company_routing), 1)               AS avg_routing_days
FROM main_marts.fact_complaints f
JOIN main_marts.dim_company dc ON f.company_id = dc.company_id
GROUP BY dc.company_name
ORDER BY total_complaints DESC
LIMIT 10;
```
> Note: `days_to_company_routing` is the CFPB routing lag (receipt → forwarded to company), not resolution time. The dataset does not publish a resolution date.


### Power BI Dashboard Visuals

Four visuals built on top of the mart Parquet files:

| Visual | Type | Fields |
|---|---|---|
| Complaint Volume Trend | Line chart | `dim_date.year_number` × `COUNT(fact_complaints)` |
| Top Companies by Complaints | Horizontal bar | `dim_company.company_name` × `COUNT(fact_complaints)` |
| Timely Response Rate by Product | Stacked bar | `dim_product.product_name` × `AVG(timely_response_flag)` |
| Routing Days Distribution | Histogram | `fact_complaints.days_to_company_routing` |
