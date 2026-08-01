{{
    config(
        materialized='table',
        description='Dimension: one row per standardized product + sub_product combination.'
    )
}}

/*
  dim_product
  ───────────
  One row per distinct (product_standardized, sub_product) combination
  from the cleaned complaints. Uses the standardized product label from
  the intermediate layer.
*/

SELECT
    ROW_NUMBER() OVER (
        ORDER BY product_standardized ASC, sub_product ASC NULLS LAST
    )                           AS product_id,
    product_standardized        AS product_name,
    sub_product                 AS sub_product_name
FROM (
    SELECT DISTINCT
        product_standardized,
        sub_product
    FROM {{ ref('int_complaints_cleaned') }}
    WHERE product_standardized IS NOT NULL
) t
