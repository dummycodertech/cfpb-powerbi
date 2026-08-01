{{
    config(
        materialized='table',
        description='Fact table. Grain: one row per unique complaint_id. All FKs point to dimension tables.'
    )
}}

/*
  fact_complaints
  ───────────────
  Central fact table. Grain: one complaint per row.

  Foreign keys:
    - date_received_key  → dim_date.date_key
    - company_id         → dim_company.company_id
    - product_id         → dim_product.product_id
    - state_code         → dim_state.state_code

  Measures stored here:
    - days_to_company_routing  (routing lag, NOT resolution time)
    - timely_response_flag     (boolean)

  Measures computed in BI layer (not stored):
    - complaint_count          → COUNTROWS(fact_complaints)
    - timely_response_rate     → DIVIDE(SUM(timely_response_flag), COUNT(*))
*/

WITH companies AS (
    SELECT company_id, company_name
    FROM {{ ref('dim_company') }}
),

products AS (
    SELECT product_id, product_name, sub_product_name
    FROM {{ ref('dim_product') }}
),

complaints AS (
    SELECT * FROM {{ ref('int_complaints_cleaned') }}
)

SELECT
    c.complaint_id,

    -- Date FK (matched to dim_date.date_key)
    c.date_received                     AS date_received_key,

    -- Company FK
    co.company_id,

    -- Product FK
    p.product_id,

    -- State FK (natural key — state_code is a 2-letter code)
    c.state                             AS state_code,

    -- Measures
    c.days_to_company_routing,
    c.timely_response_flag,

    -- Descriptive attributes kept in fact for analytical flexibility
    c.submitted_via,
    c.company_response,

    -- Degenerate dimensions (high cardinality — not promoted to dims)
    c.issue,
    c.tags

FROM complaints c
LEFT JOIN companies co
    ON c.company = co.company_name
LEFT JOIN products p
    ON c.product_standardized = p.product_name
    AND COALESCE(c.sub_product, '') = COALESCE(p.sub_product_name, '')
