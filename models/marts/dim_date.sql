{{
    config(
        materialized='table',
        description='Date dimension generated from DuckDB RANGE(). Covers full CFPB complaint history 2011-2026.'
    )
}}

/*
  dim_date
  ────────
  Date dimension generated entirely from DuckDB's native RANGE() function.
  No dependency on raw complaint data — runs independently.

  Date range: 2011-01-01 to 2026-12-31
  CFPB began accepting complaints in 2011; 2026-12-31 provides headroom
  for the current year.

  No dbt_utils dependency required — DuckDB's RANGE() is preferred over
  a date spine macro for simplicity and performance on a local engine.
*/

WITH date_spine AS (
    SELECT CAST(RANGE AS DATE) AS date_key
    FROM RANGE(
        DATE '2011-01-01',
        DATE '2027-01-01',
        INTERVAL 1 DAY
    )
)

SELECT
    date_key,
    YEAR(date_key)                              AS year_number,
    QUARTER(date_key)                           AS quarter_number,
    MONTH(date_key)                             AS month_number,
    MONTHNAME(date_key)                         AS month_name,
    DAY(date_key)                               AS day_of_month,
    DAYNAME(date_key)                           AS day_name,
    WEEKOFYEAR(date_key)                        AS week_of_year,
    DATE_TRUNC('month', date_key)::DATE         AS first_day_of_month,
    DATE_TRUNC('year',  date_key)::DATE         AS first_day_of_year,
    -- Fiscal year: assume calendar year (CFPB uses Oct-Sep; adjust here if needed)
    YEAR(date_key)                              AS fiscal_year,
    CASE
        WHEN DAYOFWEEK(date_key) IN (0, 6) THEN TRUE
        ELSE FALSE
    END                                         AS is_weekend
FROM date_spine
