import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.enums import TA_LEFT

# Changed path to local docs directory
DOC_PATH = "docs/cfpb-project-study-guide.pdf"

styles = getSampleStyleSheet()
navy = colors.HexColor("#1f2d3d")
slate = colors.HexColor("#4a5568")
accent = colors.HexColor("#2b6cb0")
light_grid = colors.HexColor("#cbd5e0")
header_bg = colors.HexColor("#edf2f7")
warn_bg = colors.HexColor("#fff7ed")

styles.add(ParagraphStyle(name="DocTitle", fontName="Helvetica-Bold", fontSize=20,
                           textColor=navy, spaceAfter=4, alignment=TA_LEFT, leading=24))
styles.add(ParagraphStyle(name="DocSubtitle", fontName="Helvetica", fontSize=11,
                           textColor=slate, spaceAfter=18, leading=14))
styles.add(ParagraphStyle(name="H1", fontName="Helvetica-Bold", fontSize=15,
                           textColor=navy, spaceBefore=18, spaceAfter=8, leading=18))
styles.add(ParagraphStyle(name="H2", fontName="Helvetica-Bold", fontSize=11.5,
                           textColor=accent, spaceBefore=12, spaceAfter=6, leading=14))
styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=9.7,
                           textColor=colors.HexColor("#1a202c"), leading=14, spaceAfter=6))
styles.add(ParagraphStyle(name="BodyItalic", fontName="Helvetica-Oblique", fontSize=9.5,
                           textColor=slate, leading=13, spaceAfter=6))
styles.add(ParagraphStyle(name="TableCell", fontName="Helvetica", fontSize=8.7,
                           textColor=colors.HexColor("#1a202c"), leading=11.5))
styles.add(ParagraphStyle(name="TableCellBold", fontName="Helvetica-Bold", fontSize=8.7,
                           textColor=navy, leading=11.5))
styles.add(ParagraphStyle(name="QLabel", fontName="Helvetica-Bold", fontSize=9.8,
                           textColor=accent, spaceBefore=10, spaceAfter=2, leading=13))
styles.add(ParagraphStyle(name="ALabel", fontName="Helvetica", fontSize=9.5,
                           textColor=colors.HexColor("#1a202c"), leading=13.5, spaceAfter=4,
                           leftIndent=12))
styles.add(ParagraphStyle(name="GlossTerm", fontName="Helvetica-Bold", fontSize=9.5,
                           textColor=navy, leading=13))
styles.add(ParagraphStyle(name="GlossDef", fontName="Helvetica", fontSize=9.3,
                           textColor=colors.HexColor("#1a202c"), leading=12.5, spaceAfter=7))
styles.add(ParagraphStyle(name="MathLine", fontName="Helvetica", fontSize=10.5,
                           textColor=navy, leading=16, spaceAfter=3, leftIndent=10))
styles.add(ParagraphStyle(name="MathLineBold", fontName="Helvetica-Bold", fontSize=10.8,
                           textColor=navy, leading=17, spaceAfter=3, leftIndent=10))

def P(text, style="Body"):
    return Paragraph(text, styles[style])

def rule():
    return HRFlowable(width="100%", thickness=0.6, color=light_grid, spaceBefore=2, spaceAfter=10)

def make_table(header, rows, col_widths, header_bg_color=header_bg):
    data = [[Paragraph(h, styles["TableCellBold"]) for h in header]]
    for r in rows:
        data.append([Paragraph(str(c), styles["TableCell"]) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg_color),
        ("GRID", (0, 0), (-1, -1), 0.5, light_grid),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t

def bullets(items):
    return ListFlowable(
        [ListItem(P(i), leftIndent=6, spaceAfter=4) for i in items],
        bulletType="bullet", start="\u2022", leftIndent=14,
    )

story = []

# ------------------------------------------------------------- Title ---
story.append(P("CFPB Consumer Complaints Warehouse", "DocTitle"))
story.append(P("Interview study guide &mdash; dbt + DuckDB + Power BI project, built by Yagas Vashist. "
               "Written to be read with zero prior dbt/analytics-engineering background: every number "
               "is traced back to how it was actually calculated, every command is explained, and one "
               "complaint is walked through the full pipeline as a worked example.", "DocSubtitle"))
story.append(rule())

# ------------------------------------------------------ 1. Overview ---
story.append(P("1. Project overview", "H1"))
story.append(P(
    "This project turns CFPB's public Consumer Complaint Database &mdash; roughly 16.8 million real "
    "complaint records against banks, lenders, and credit reporting agencies &mdash; into a tested, "
    "documented analytics warehouse. dbt-core handles transformation and testing, DuckDB is the "
    "embedded engine, and Power BI sits on top as the presentation layer. The point of the project "
    "isn't the dashboard &mdash; it's proving the pipeline underneath the dashboard is correct, "
    "tested, and defensible.", "Body"))

story.append(P("Key numbers (final, verified run)", "H2"))
story.append(make_table(
    ["Metric", "Value"],
    [
        ["Data snapshot date", "2026-08-01"],
        ["Raw rows ingested", "16,849,715"],
        ["Fact rows (final)", "16,848,394"],
        ["Rows excluded at staging", "1,321"],
        ["Distinct companies", "8,033"],
        ["Distinct product / sub-product combos", "105"],
        ["dbt models", "7 (1 staging, 1 intermediate, 5 marts)"],
        ["dbt tests", "35 (34 pass, 1 warn, 0 error)"],
        ["dbt total nodes (models + seed + tests)", "43"],
        ["dbt build runtime", "63.23 seconds"],
        ["Parquet export size (fact_complaints)", "79.15 MB, ZSTD compressed"],
    ],
    [230, 234],
))

# ------------------------------------------------- 2. Arithmetic walkthrough ---
story.append(P("2. How the numbers reconcile &mdash; the actual arithmetic", "H1"))
story.append(P(
    "This is the section to actually understand, not just memorize. Every count in this project "
    "traces back to one subtraction, done in two steps.", "Body"))

story.append(P("Step 1 &mdash; raw to fact", "H2"))
story.append(P("16,849,715 &nbsp;&nbsp;(raw rows loaded from the CFPB export, untouched)", "MathLine"))
story.append(P("&minus; 1,321 &nbsp;&nbsp;(rows excluded by the staging layer &mdash; see step 2)",
               "MathLine"))
story.append(P("= 16,848,394 &nbsp;&nbsp;(rows in fact_complaints, the final count)", "MathLineBold"))

story.append(P("Step 2 &mdash; what makes up the 1,321 exclusions", "H2"))
story.append(P("11 &nbsp;&nbsp;(CSV multiline parse failures)", "MathLine"))
story.append(P("+ 1,310 &nbsp;&nbsp;(CFPB \u201cPending Company Match\u201d records)", "MathLine"))
story.append(P("= 1,321 &nbsp;&nbsp;(total exclusions, matches step 1)", "MathLineBold"))

story.append(P("Why the 11 parse failures happen", "H2"))
story.append(P(
    "CFPB's free-text complaint narrative field can legitimately contain a literal newline "
    "character &mdash; a consumer's complaint text can span multiple lines. A properly quoted CSV "
    "handles this fine (the whole field, newline included, sits inside one pair of quotes). If a row "
    "isn't quoted correctly in the source export, a naive parser reads that embedded newline as "
    "\u201cend of row\u201d and splits one real complaint into two broken rows &mdash; the second "
    "fragment has no ID, no date, nothing usable. That's what these 11 rows are: confirmed by "
    "inspection, not assumed.", "Body"))

story.append(P("Why the 1,310 Pending Company Match rows happen", "H2"))
story.append(P(
    "A CFPB complaint goes through a lifecycle: submitted by the consumer, reviewed by CFPB, then "
    "routed to the company it's about. The Complaint ID is assigned as part of that routing step. "
    "These 1,310 rows are complaints that have cleared the first steps &mdash; they have a real "
    "date, a real state, a real product category &mdash; but haven't reached routing yet, so there's "
    "no ID. They are not bad data. They're excluded from fact_complaints for a structural reason, "
    "not a quality reason: the fact table's grain is \u201cone row per complaint_id,\u201d and a "
    "table can't enforce uniqueness or support reliable joins on a key that's null.", "Body"))

story.append(P("Why this distinction matters for an interview", "H2"))
story.append(P(
    "Anyone can say \u201cI dropped 1,321 null rows.\u201d The stronger answer is knowing that 11 of "
    "them are a genuine parsing defect and 1,310 of them are a completely different, non-defective "
    "category that just structurally can't fit a star schema yet. Conflating the two would be the "
    "naive-cleaning answer this project is specifically built to avoid.", "Body"))

# ------------------------------------------------------ 3. Architecture ---
story.append(PageBreak())
story.append(P("3. Architecture walkthrough", "H1"))
story.append(P(
    "Five stages, each independently re-runnable. The important thing to be able to explain isn't "
    "just what each stage does &mdash; it's why the boundary between stages is drawn where it is.",
    "Body"))

arch_rows = [
    ["1. Raw ingestion", "Load the CFPB CSV unmodified into DuckDB, every column as VARCHAR.",
     "Preserves source fidelity. If a downstream transformation turns out wrong, you rebuild from "
     "raw without re-downloading or re-trusting a cleaned copy."],
    ["2. Staging", "1:1 with the source: rename to snake_case, cast dates and IDs. No business logic.",
     "Separates structural cleanup (types, names) from business logic, so a broken cast is easy to "
     "isolate and never hides inside a business rule."],
    ["3. Intermediate", "Dedup on complaint_id, standardize product labels across filing years, "
     "derive days_to_company_routing.",
     "Keeps business logic in one auditable layer that can change without touching what the marts "
     "or the dashboard consume."],
    ["4. Marts", "Star schema: fact_complaints plus dim_company, dim_product, dim_state, dim_date.",
     "This is the shape BI tools actually query. A star schema keeps joins simple and query "
     "performance predictable at scale."],
    ["5. Presentation", "Export marts to Parquet; Power BI reads Parquet directly.",
     "Avoids a fragile ODBC driver dependency and keeps the project portable to any BI tool, not "
     "just Power BI."],
]
story.append(make_table(["Stage", "What it does", "Why the boundary is there"], arch_rows,
                         [70, 175, 219]))

# ------------------------------------------------------ 4. Workflow ---
story.append(P("4. Step-by-step workflow &mdash; what each command actually does", "H1"))
story.append(P(
    "This is the same sequence as the README's setup instructions, with the \u201cwhy\u201d filled "
    "in for each step.", "Body"))

wf_rows = [
    ["python -m venv .venv &nbsp;/&nbsp; activate",
     "Creates an isolated Python environment scoped to this project, so its exact package versions "
     "never conflict with anything else installed on the machine."],
    ["pip install -r requirements.txt",
     "Installs dbt-core, the dbt-duckdb adapter, and the duckdb library &mdash; everything the "
     "pipeline needs, pinned to known-working versions."],
    ["python scripts/01_download.py",
     "Downloads the ~330 MB zipped CFPB export from the government's public bulk URL and unzips it "
     "locally. Nothing is parsed or interpreted yet, just fetched."],
    ["python scripts/02_ingest.py",
     "Creates the local DuckDB file and loads the raw CSV directly into a table called "
     "raw_complaints, with every column stored as text (VARCHAR). No cleaning, casting, or "
     "renaming happens at this step &mdash; it's a faithful copy of the source."],
    ["dbt seed --profiles-dir .",
     "Loads the small us_states.csv lookup file (state code, state name, Census region) into DuckDB "
     "as a real table &mdash; this becomes the basis for dim_state."],
    ["dbt build --profiles-dir .",
     "The core step. dbt reads every .sql file under models/, works out which models depend on "
     "which others via their ref() calls, runs them in the correct dependency order (staging, then "
     "intermediate, then marts), and after each model finishes, runs whatever tests are configured "
     "for it in that layer's schema.yml."],
    ["dbt docs generate &nbsp;+&nbsp; dbt docs serve",
     "Turns the project's model and column metadata into a browsable local website, including the "
     "interactive lineage graph (the DAG) showing exactly how every table depends on every other."],
    ["python scripts/04_export_parquet.py",
     "Reads each finished mart table out of DuckDB and writes it to a .parquet file, which Power BI "
     "can open directly with no driver or database connection required."],
]
story.append(make_table(["Command", "What it does and why"], wf_rows, [140, 314]))

# ------------------------------------------------ 5. Worked example ---
story.append(PageBreak())
story.append(P("5. A worked example &mdash; one complaint's journey through the pipeline", "H1"))
story.append(P(
    "The table below is an illustrative example built to show the transformation clearly &mdash; not "
    "an actual extracted record. It follows one hypothetical complaint through all five layers.",
    "BodyItalic"))

story.append(P("Raw layer (all columns VARCHAR, no changes)", "H2"))
story.append(make_table(
    ["Column", "Value"],
    [
        ["Complaint ID", "\"9284017\""],
        ["Date received", "\"03/14/2024\""],
        ["Product", "\"Credit Card or prepaid card\""],
        ["Date sent to company", "\"03/19/2024\""],
        ["Timely response?", "\"Yes\""],
    ],
    [140, 314],
))

story.append(P("Staging layer (renamed, cast, no business logic)", "H2"))
story.append(make_table(
    ["Column", "Value"],
    [
        ["complaint_id (BIGINT)", "9284017"],
        ["date_received (DATE)", "2024-03-14"],
        ["product (VARCHAR, unchanged)", "Credit Card or prepaid card"],
        ["date_sent_to_company (DATE)", "2024-03-19"],
        ["timely_response (VARCHAR, unchanged)", "Yes"],
    ],
    [180, 274],
))

story.append(P("Intermediate layer (business logic applied)", "H2"))
story.append(make_table(
    ["Column", "Value"],
    [
        ["complaint_id", "9284017"],
        ["product_standardized", "Credit Card / Prepaid Card &nbsp;(mapped from the raw label)"],
        ["days_to_company_routing", "5 &nbsp;(2024-03-19 minus 2024-03-14)"],
        ["timely_response_flag (BOOLEAN)", "TRUE"],
    ],
    [180, 274],
))

story.append(P("Marts layer (split into fact + dimension references)", "H2"))
story.append(make_table(
    ["Table", "What it holds for this complaint"],
    [
        ["fact_complaints", "complaint_id=9284017, product_id=&lt;lookup&gt;, date_received_key="
                             "&lt;lookup&gt;, days_to_company_routing=5, timely_response_flag=TRUE"],
        ["dim_product", "The row where product_name = \u2018Credit Card / Prepaid Card\u2019 &mdash; "
                         "referenced by product_id, not repeated on every fact row"],
        ["dim_date", "The row where date_key corresponds to 2024-03-14, carrying year/month/quarter/"
                      "day-of-week &mdash; also referenced, not repeated"],
    ],
    [110, 344],
))
story.append(Spacer(1, 4))
story.append(P(
    "This is the actual point of a star schema: the fact row stays narrow (just keys and measures), "
    "and everything descriptive &mdash; the full product name, the calendar attributes &mdash; lives "
    "once in a dimension table and gets referenced, not repeated 16.8 million times.", "Body"))

# ------------------------------------------------------ 6. Concepts primer ---
story.append(PageBreak())
story.append(P("6. Core concepts &mdash; what you need to actually know, not just recite", "H1"))

story.append(P("dbt and the staging &rarr; intermediate &rarr; marts pattern", "H2"))
story.append(P(
    "dbt (data build tool) turns SQL into a managed project: models are just SELECT statements in "
    ".sql files, and dbt figures out the run order automatically from ref() calls between them "
    "&mdash; that dependency graph is the DAG you see in dbt docs. Layering models into staging, "
    "intermediate, and marts isn't a dbt requirement, it's a convention that keeps each layer doing "
    "one job: staging cleans structure, intermediate applies business logic, marts is what gets "
    "queried.", "Body"))

story.append(P("Star schema, grain, fact vs. dimension", "H2"))
story.append(P(
    "A fact table holds events or transactions at a defined <b>grain</b> &mdash; the grain answers "
    "\u201cwhat does one row mean?\u201d Here, the grain of fact_complaints is one row per "
    "complaint_id. Dimension tables hold descriptive context (company name, product name, state, "
    "date attributes) that the fact table references by key, as shown in the worked example above.",
    "Body"))

story.append(P("Why DuckDB", "H2"))
story.append(P(
    "DuckDB is an embedded, in-process, columnar OLAP engine &mdash; no server, no setup, just a "
    "file. Columnar storage means it reads only the columns a query touches instead of whole rows, "
    "which is exactly the access pattern analytical aggregation needs. Row-oriented engines like "
    "Postgres or SQLite are built for OLTP workloads (many small reads and writes of individual "
    "rows), not for scanning and aggregating millions of rows at once.", "Body"))

story.append(P("Materialization: why views here, tables there", "H2"))
story.append(P(
    "Staging and intermediate models are materialized as <b>views</b> &mdash; they cost nothing to "
    "store and always reflect the latest model logic on every query. Marts are materialized as "
    "<b>tables</b> &mdash; they cost storage and a rebuild on every dbt run, but Power BI hits them "
    "repeatedly, so paying the computation cost once per build is the right trade rather than "
    "recomputing the whole transformation chain on every dashboard refresh.", "Body"))

story.append(P("dbt tests: types and severity", "H2"))
story.append(make_table(
    ["Test type", "What it checks"],
    [
        ["not_null", "The column never contains a null value."],
        ["unique", "Every value in the column appears exactly once."],
        ["relationships", "Every value in this column exists in the referenced table's key column "
                           "&mdash; referential integrity, i.e. a foreign-key check."],
        ["accepted_values", "The column only ever contains values from a fixed, defined list."],
    ],
    [110, 344],
))
story.append(Spacer(1, 6))
story.append(P(
    "Severity is a separate axis from the test type: <b>error</b> severity fails the whole "
    "dbt build; <b>warn</b> severity logs the failure but lets the build succeed. This project uses "
    "warn where the \u201cviolation\u201d is real, legitimate data &mdash; military postal codes "
    "(AA/AE/AP) not in the state seed, for example &mdash; rather than an actual defect.", "Body"))

# ------------------------------------------------------ 7. Design decisions ---
story.append(PageBreak())
story.append(P("7. Design decisions and their defensible rationale", "H1"))
story.append(P(
    "Every row here is a question an interviewer could reasonably ask &mdash; \u201cwhy did you do "
    "X and not Y\u201d &mdash; with the answer already worked out.", "Body"))

dec_rows = [
    ["Parquet export, not DuckDB ODBC, for Power BI",
     "DuckDB's Windows ODBC driver has known compatibility issues with Power BI Desktop. Parquet "
     "needs no driver install and is portable to any BI tool, not just Power BI."],
    ["profiles.yml committed to the repo",
     "Contains only a local DuckDB file path, no credentials. Committed deliberately for one-"
     "command reproducibility on a solo/local project &mdash; explicitly acknowledged as non-"
     "standard for a team or production repo, where it would hold credentials and stay out of "
     "version control."],
    ["Field named days_to_company_routing, not \u201cresolution time\u201d",
     "CFPB publishes only a routing date (when a complaint was forwarded to the company), not an "
     "actual resolution date. Naming the field for what the data really measures avoids overclaiming "
     "what the metric can support."],
    ["Warn, not error, severity on 3 specific tests",
     "state_code relationship, timely_response not_null, and submitted_via accepted_values are all "
     "warn-severity because the underlying condition is real, valid data (military postal codes, "
     "in-progress complaints) &mdash; failing the entire build over legitimate data would be the "
     "wrong trade-off."],
    ["complaint_id cast to BIGINT, not INTEGER",
     "No functional need at 16.8M rows today, but removes any doubt about integer overflow as the "
     "dataset grows &mdash; zero cost, permanently removes a class of bug."],
    ["Dedup on complaint_id, keep-latest by date_received",
     "Keeps fact_complaints at a clean one-row-per-complaint grain, which every downstream join and "
     "every BI aggregate implicitly depends on."],
    ["Test-break injection uses a fabricated sentinel ID, not a real complaint_id",
     "Duplicating a real ID meant cleanup had to guess which of two identical-looking rows to "
     "delete &mdash; that ambiguity is what caused a real row to be lost the first time. A "
     "fabricated ID that can never collide with real data makes cleanup unambiguous and safe to "
     "re-run."],
]
story.append(make_table(["Decision", "Why it's defensible"], dec_rows, [150, 304]))

# ------------------------------------------------------ 8. Real findings ---
story.append(PageBreak())
story.append(P("8. The two real findings in the data", "H1"))

story.append(P("8a. Zero organic duplicate complaint IDs", "H2"))
story.append(P(
    "Running the unique test against all 16.8 million real rows produced zero failures &mdash; "
    "bureau-assigned IDs are clean. That result alone doesn't prove the test works, though; it only "
    "proves the data happens to be clean. To actually verify the test catches what it's supposed to "
    "catch, two rows sharing a deliberately fabricated ID were injected, the test was confirmed to "
    "fail, and the injection was then removed. That's a stronger claim than \u201cI wrote a "
    "test\u201d &mdash; it's \u201cI proved the test catches what it's built to catch.\u201d", "Body"))

story.append(P("8b. CFPB \u201cPending Company Match\u201d records", "H2"))
story.append(P(
    "1,310 rows have a null complaint_id but otherwise valid dates, companies, and states &mdash; "
    "see section 2 for the full explanation of why. They're excluded from fact_complaints because "
    "the fact table's grain requires a primary key, and documented as a named category rather than "
    "silently dropped. This shows understanding of the source system's actual lifecycle, not just "
    "its file format.", "Body"))

# ------------------------------------------------------ 9. The bug ---
story.append(P("9. The bug, and what it's actually worth in an interview", "H1"))
story.append(P(
    "While verifying the unique test, the original injection script duplicated a real, existing "
    "complaint_id, then removed the duplicate as part of cleanup &mdash; but the cleanup logic "
    "wasn't scoped precisely enough, and it also deleted the original real row sharing that ID. One "
    "legitimate record was permanently lost from the raw table.", "Body"))
story.append(P(
    "Root cause: the test mutated a shared, real table using an ID it didn't fully own &mdash; once "
    "two rows had the same ID, nothing distinguished \u201cthe one I added\u201d from \u201cthe one "
    "that was already there.\u201d", "Body"))
story.append(P(
    "The fix: inject rows using a fabricated sentinel ID that is guaranteed not to collide with any "
    "real CFPB complaint_id. Cleanup then deletes only rows matching that exact sentinel value, "
    "which can never touch real data, because no real row will ever carry that ID.", "Body"))
story.append(P(
    "How the original bug was found: the raw ingestion count (16,849,715) didn't reconcile with the "
    "current raw row count after rebuilding the fact table &mdash; the arithmetic was off by exactly "
    "one row, which is what surfaced the deletion. This is the same reconciliation discipline used "
    "in section 2 to explain every other number in this project.", "Body"))
story.append(P(
    "Why this is a genuinely good interview answer: it's a real, specific, technical mistake with a "
    "clear root cause and a concrete fix &mdash; far stronger than a vague \u201cI sometimes make "
    "mistakes but I learn from them.\u201d Suggested structure for \u201ctell me about a mistake you "
    "made\u201d: what happened, why (an ID-based cleanup with no way to distinguish injected from "
    "real), how it was caught (a reconciliation check that didn't add up), and the fix (a sentinel "
    "ID that structurally cannot collide with real data).", "Body"))

# ------------------------------------------------------ 10. Interview Q&A ---
story.append(PageBreak())
story.append(P("10. Likely interview questions and talking points", "H1"))

qa = [
    ("Why dbt instead of plain SQL scripts?",
     "dbt adds dependency management &mdash; it derives run order from ref() calls &mdash; plus "
     "built-in testing and auto-generated documentation and lineage. The same SQL without dbt would "
     "need all of that built by hand."),
    ("Why DuckDB instead of Postgres or SQLite?",
     "DuckDB is columnar and in-process, built for scanning and aggregating large read-heavy "
     "datasets fast with zero setup. Postgres and SQLite are row-oriented, built for transactional "
     "workloads, not analytical scans across millions of rows."),
    ("What's the grain of your fact table?",
     "One row per complaint_id. Every measure and every join assumes that grain, which is exactly "
     "why the uniqueness test on complaint_id in the fact table is non-negotiable."),
    ("Walk me through what happens when you run dbt build.",
     "dbt reads the dependency graph built from ref() calls, determines run order, materializes "
     "each model as configured (view or table), then runs the tests configured against the results "
     "&mdash; failing or warning per each test's severity."),
    ("How did your raw and fact row counts reconcile?",
     "16,849,715 raw rows minus 1,321 exclusions equals 16,848,394 fact rows. The 1,321 splits into "
     "11 genuine CSV parse failures and 1,310 CFPB Pending Company Match records &mdash; see the "
     "arithmetic walkthrough in section 2 for the full reasoning behind each category."),
    ("What would you do differently in production?",
     "Incremental loading instead of a full rebuild each run, an orchestrator like Airflow or "
     "Dagster instead of a manual setup script, real secrets management instead of a locally "
     "committed profiles.yml, and CI running dbt tests on every pull request before merge."),
    ("Tell me about a mistake you made on this project.",
     "The original test-break cleanup script deleted a real row alongside the injected one, because "
     "it duplicated a real ID instead of using a fabricated one &mdash; see section 9 for the full "
     "structure of this answer."),
    ("Why isn't your routing-time field called \u201cresolution time\u201d?",
     "CFPB doesn't publish an actual resolution date, only a routing date. Naming the field "
     "accurately avoids claiming a metric the data can't support."),
    ("How do you know your dedup logic actually works, if you found zero real duplicates?",
     "Zero real duplicates only proves the data is clean, not that the test works. A duplicate was "
     "deliberately injected using a fabricated ID to confirm the test fails when it should, then "
     "removed safely."),
    ("What are the Pending Company Match rows, and why exclude them?",
     "Complaints still in CFPB's internal routing queue, not yet assigned an ID &mdash; valid "
     "records, just structurally unable to join into a star schema that requires a primary key."),
    ("Why views for staging and intermediate, but tables for marts?",
     "Views cost nothing to store and stay current automatically; marts are queried repeatedly by "
     "Power BI, so materializing them as tables trades a one-time build cost for much faster repeat "
     "queries."),
    ("What's a surrogate key, and where do you use one?",
     "A generated key (for example, via ROW_NUMBER()) used when the source doesn't provide a "
     "natural unique identifier. company_id and product_id are surrogate keys generated in the "
     "marts layer, since the raw data only has names, not IDs."),
    ("Why warn instead of error on the state_code relationship test?",
     "2,027 rows have state codes like AA, AE, or AP &mdash; real military postal codes not covered "
     "by the state seed. Failing the whole build over legitimate data would be the wrong trade-off; "
     "warn keeps the condition visible without blocking the pipeline."),
]

for q, a in qa:
    story.append(KeepTogether([P(q, "QLabel"), P(a, "ALabel")]))

# ------------------------------------------------------ 11. Glossary ---
story.append(PageBreak())
story.append(P("11. Glossary", "H1"))

glossary = [
    ("dbt (data build tool)", "An open-source framework that turns SQL SELECT statements into a "
     "managed project with dependency resolution, testing, and documentation."),
    ("DAG", "Directed acyclic graph &mdash; the dependency chain between models, derived automatically "
     "from ref() calls, with no circular dependencies allowed."),
    ("Materialization", "How a dbt model is physically built: as a view (query run live each time) "
     "or a table (query run once, result stored)."),
    ("Grain", "The definition of what one row in a table represents &mdash; e.g. \u201cone row per "
     "complaint.\u201d Every measure and join in a model implicitly assumes its grain."),
    ("Star schema", "A modeling pattern with one central fact table joined to surrounding dimension "
     "tables, shaped like a star when diagrammed."),
    ("Fact table", "Holds events or transactions at a defined grain, referencing dimensions by key."),
    ("Dimension table", "Holds descriptive context (names, categories, dates) that a fact table "
     "references, typically wide and slowly changing."),
    ("Surrogate key", "An artificially generated identifier (e.g. via ROW_NUMBER()) used when the "
     "source system has no natural unique key."),
    ("Natural key", "An identifier that already exists in the source data, such as CFPB's own "
     "complaint_id."),
    ("Sentinel value", "A deliberately chosen value guaranteed not to occur in real data, used to "
     "mark or test something safely &mdash; the fabricated ID used in the fixed test-break script "
     "is a sentinel value."),
    ("Idempotent", "A process that produces the same result no matter how many times it's re-run "
     "with the same input &mdash; important for pipelines that might be re-triggered."),
    ("Lineage", "The traceable path of how a piece of data flowed from source to final output, "
     "visualized by dbt docs as the DAG."),
    ("ODBC", "Open Database Connectivity &mdash; a standard driver interface that lets tools like "
     "Power BI connect to a database; DuckDB's ODBC support on Windows is not fully reliable."),
    ("Parquet", "A columnar file format for storing tabular data efficiently and compactly, readable "
     "natively by most modern BI and data tools without a database connection."),
    ("Columnar storage", "Data stored column-by-column rather than row-by-row, so a query only reads "
     "the columns it actually needs &mdash; ideal for analytical aggregation."),
    ("OLAP vs. OLTP", "OLAP (online analytical processing) is optimized for large read-heavy "
     "aggregation queries; OLTP (online transactional processing) is optimized for many small, "
     "frequent reads and writes of individual records."),
    ("Seed", "A dbt term for a small reference dataset (e.g. a state-code lookup CSV) loaded into "
     "the warehouse directly from a file in the repo, via dbt seed."),
    ("ref() function", "The dbt macro used inside a model to reference another model, which is how "
     "dbt builds the dependency graph automatically."),
]

for term, definition in glossary:
    story.append(KeepTogether([P(term, "GlossTerm"), P(definition, "GlossDef")]))

# ------------------------------------------------------ 12. Limitations ---
story.append(PageBreak())
story.append(P("12. Known limitations &mdash; know these before someone else points them out", "H1"))
story.append(bullets([
    "Full-snapshot load, not incremental &mdash; every run rebuilds from the complete CFPB export. "
    "Fine at this scale and frequency; a true production pipeline updating daily or hourly would use "
    "dbt's incremental materialization instead.",
    "dim_state's seed doesn't cover military postal codes (AA, AE, AP) &mdash; acknowledged "
    "explicitly via the warn-severity relationship test rather than silently ignored.",
    "No CI/CD &mdash; tests currently run manually via dbt build, not gated automatically on every "
    "change to the repo.",
    "No orchestration tool &mdash; the manual setup.ps1 script stands in for what would be an "
    "Airflow or Dagster DAG in a real production analog.",
]))

story.append(Spacer(1, 10))
story.append(P("Before the interview, actually do this", "H2"))
story.append(bullets([
    "Re-run scripts/03_inject_test_break.py end to end and confirm raw count returns to "
    "16,849,715 unchanged afterward &mdash; that's the real proof the fix works, not the fact that "
    "the number looks right today.",
    "Open dbt docs and click through the lineage graph once more so you can describe it without "
    "looking at this guide.",
    "Re-run the sample query in the README from memory, out loud, once.",
]))

story.append(Spacer(1, 14))
story.append(rule())
story.append(P(
    "Study approach: read sections 2, 4, and 5 first &mdash; those build the actual understanding. "
    "Section 10 is what interview questions will look like; section 9 is the strongest single story "
    "in this whole document. Know it well enough to tell it without notes.", "BodyItalic"))

doc = SimpleDocTemplate(
    DOC_PATH, pagesize=letter,
    leftMargin=54, rightMargin=54, topMargin=48, bottomMargin=48,
    title="CFPB Consumer Complaints Warehouse - Interview Study Guide",
    author="Yagas Vashist",
)
doc.build(story)
print("done")
