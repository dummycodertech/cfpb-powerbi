{{
    config(
        materialized='table',
        description='Dimension: one row per distinct company. Surrogate key via ROW_NUMBER.'
    )
}}

/*
  dim_company
  ───────────
  One row per distinct company name from the cleaned complaints.

  No pre-aggregated metrics are stored here.
  Complaint counts belong in the fact layer and should be computed as
  Power BI measures (e.g. COUNTROWS(fact_complaints)) to maintain
  strict star-schema separation.
*/

SELECT
    ROW_NUMBER() OVER (ORDER BY company ASC)  AS company_id,
    company                                   AS company_name
FROM (
    SELECT DISTINCT company
    FROM {{ ref('int_complaints_cleaned') }}
    WHERE company IS NOT NULL
) t
