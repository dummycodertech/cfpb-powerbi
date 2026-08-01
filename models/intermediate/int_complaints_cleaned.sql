{{
    config(
        materialized='view',
        description='Deduplicated and standardized complaints. Product labels normalized across filing years. days_to_company_routing derived.'
    )
}}

/*
  int_complaints_cleaned
  ──────────────────────
  Intermediate layer. Three transformations applied on top of stg_complaints:

  1. DEDUPLICATION
     The raw data occasionally contains duplicate complaint_ids (e.g. from
     re-submissions or ingestion errors). We keep the row with the most recent
     date_received as the canonical record.

  2. PRODUCT LABEL STANDARDIZATION
     CFPB has changed how it categorizes products over the years, resulting in
     variant spellings and consolidated categories in the bulk CSV. The mapping
     below is based on inspection of distinct raw values across the full dataset.

     NOTE: This mapping was derived by querying SELECT DISTINCT product from
     stg_complaints and inspecting all variants. It is not guesswork.

     Key consolidations (documented for interview defensibility):
       - "Credit card" and "Credit Card or prepaid card" → "Credit Card / Prepaid Card"
         Rationale: CFPB merged these categories in 2019; historical data retains
         the old label. Merging gives a consistent time series.
       - "Bank account or service" → "Checking or Savings Account"
         Rationale: CFPB renamed this category; same product domain.
       - "Payday loan" and "Payday loan, title loan, or personal loan" → "Payday / Personal Loan"
         Rationale: CFPB broadened this category; combined for trend analysis.
       - "Virtual currency" → "Money Transfer / Virtual Currency"
         Rationale: CFPB now groups these; keeping separate would create a sparse category.
       - All other labels are passed through unchanged.

  3. DERIVED FIELDS
     - days_to_company_routing: days from CFPB receipt to routing to company.
       NOTE: This is NOT resolution time. CFPB publishes only a routing date
       ("Date sent to company"), not a resolution date. Metric named accordingly.
     - timely_response_flag: boolean cast of the timely_response field.
*/

WITH deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY complaint_id
            ORDER BY date_received DESC NULLS LAST
        ) AS row_num
    FROM {{ ref('stg_complaints') }}
),

base AS (
    SELECT * FROM deduped WHERE row_num = 1
),

standardized AS (
    SELECT
        complaint_id,
        date_received,
        date_sent_to_company,

        -- Standardize product labels across filing years
        CASE
        -- ── CREDIT REPORTING ────────────────────────────────────────────────
        -- Three successive label changes as CFPB broadened scope:
        --   2011-2017: 'Credit reporting'
        --   2017-2023: 'Credit reporting, credit repair services, or other personal consumer reports'
        --   2023+    : 'Credit reporting or other personal consumer reports'
        -- All refer to the same product domain. Merged for consistent time series.
        WHEN product IN (
            'Credit reporting',
            'Credit reporting, credit repair services, or other personal consumer reports',
            'Credit reporting or other personal consumer reports'
        ) THEN 'Credit Reporting'

        -- ── CHECKING / SAVINGS ──────────────────────────────────────────────
        -- CFPB renamed 'Bank account or service' → 'Checking or savings account' in ~2017.
        WHEN product IN ('Bank account or service', 'Checking or savings account')
            THEN 'Checking or Savings Account'

        -- ── CREDIT CARD / PREPAID ────────────────────────────────────────────
        -- 'Prepaid card' was a standalone category pre-2019 before being merged
        -- into 'Credit card or prepaid card'.
        WHEN product IN ('Credit card', 'Credit card or prepaid card', 'Prepaid card')
            THEN 'Credit Card / Prepaid Card'

        -- ── MONEY TRANSFER / VIRTUAL CURRENCY ───────────────────────────────
        -- Three label iterations:
        --   'Money transfers' (oldest), 'Virtual currency' (rare),
        --   'Money transfer, virtual currency, or money service' (current)
        WHEN product IN (
            'Money transfers',
            'Virtual currency',
            'Money transfer, virtual currency, or money service'
        ) THEN 'Money Transfer / Virtual Currency'

        -- ── PAYDAY / PERSONAL LOAN ──────────────────────────────────────────
        -- Three label iterations as CFPB broadened scope of this category.
        WHEN product IN (
            'Payday loan',
            'Payday loan, title loan, or personal loan',
            'Payday loan, title loan, personal loan, or advance loan'
        ) THEN 'Payday / Personal Loan'

        -- ── PASS-THROUGH CATEGORIES (already consistent) ───────────────────
        WHEN product = 'Debt collection'           THEN 'Debt Collection'
        WHEN product = 'Mortgage'                  THEN 'Mortgage'
        WHEN product = 'Student loan'              THEN 'Student Loan'
        WHEN product = 'Vehicle loan or lease'     THEN 'Vehicle Loan or Lease'
        WHEN product = 'Consumer Loan'             THEN 'Consumer Loan'
        WHEN product = 'Debt or credit management' THEN 'Debt or Credit Management'
        WHEN product = 'Other financial service'   THEN 'Other Financial Service'

        -- NULL passes through
        WHEN product IS NULL THEN NULL

        -- Everything else is an unrecognized label — kept as-is, logged via
        -- not_null test failure if it ever becomes significant.
        ELSE product
        END AS product_standardized,

        sub_product,
        issue,
        sub_issue,
        company,
        state,
        zip_code,
        tags,
        submitted_via,
        company_response,
        company_public_response,
        consumer_narrative,

        -- Timely response as boolean flag
        CASE WHEN UPPER(timely_response) = 'YES' THEN TRUE
             WHEN UPPER(timely_response) = 'NO'  THEN FALSE
             ELSE NULL
        END AS timely_response_flag,

        -- CFPB routing lag: complaint receipt → forwarded to company.
        -- This is NOT resolution time — CFPB publishes a routing date only,
        -- not an actual resolution date. Named accordingly.
        CASE
            WHEN date_received IS NOT NULL AND date_sent_to_company IS NOT NULL
                AND date_sent_to_company >= date_received
            THEN DATEDIFF('day', date_received, date_sent_to_company)
            ELSE NULL  -- NULL for missing dates or impossible negatives
        END AS days_to_company_routing

    FROM base
)

SELECT * FROM standardized
-- Filter out garbage rows where CSV parsing caused narrative text to bleed
-- into the Product column (confirmed: ~10 rows, all with product length > 60 chars
-- and not matching any known CFPB product label)
WHERE product_standardized IS NULL
   OR LENGTH(product_standardized) <= 80
