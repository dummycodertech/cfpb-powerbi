{{
    config(
        materialized='view',
        description='1:1 with raw source. Renames columns to snake_case, casts date and ID types. No business logic.'
    )
}}

/*
  stg_complaints
  ──────────────
  Staging layer: direct 1-to-1 map of raw.raw_complaints with:
    1. snake_case column renaming
    2. Type casts (dates → DATE, complaint_id → BIGINT)
    3. Whitespace trimming on key categorical fields
  No deduplication, no business logic, no derived columns.
*/

SELECT
    -- Primary key
    TRY_CAST(TRIM("Complaint ID") AS BIGINT)          AS complaint_id,

    -- Dates (raw format is ISO 8601 timestamp: 2024-03-06T11:43:05.000Z)
    TRY_CAST(TRIM("Date received")          AS DATE) AS date_received,
    TRY_CAST(TRIM("Date sent to company")   AS DATE) AS date_sent_to_company,

    -- Categorical / text columns  (trimmed, kept as VARCHAR)
    TRIM("Product")                                    AS product,
    TRIM("Sub-product")                                AS sub_product,
    TRIM("Issue")                                      AS issue,
    TRIM("Sub-issue")                                  AS sub_issue,
    TRIM("Company")                                    AS company,
    TRIM("State")                                      AS state,
    TRIM("ZIP code")                                   AS zip_code,
    TRIM("Tags")                                       AS tags,
    TRIM("Submitted via")                              AS submitted_via,
    TRIM("Company response to consumer")               AS company_response,
    TRIM("Company public response")                    AS company_public_response,
    TRIM("Timely response?")                           AS timely_response,

    -- Long text (narrative may be NULL when consent not provided)
    "Consumer complaint narrative"                     AS consumer_narrative

FROM {{ source('raw', 'raw_complaints') }}

-- Exclude rows where CSV multiline parsing broke a long complaint narrative
-- across rows, causing date or ID fields to contain narrative text.
-- Confirmed: 11 such rows exist (complaint_ids with valid duplicates in raw).
-- Also excludes ~1,310 rows with NULL complaint_id (continuation lines).
WHERE TRY_CAST(TRIM("Complaint ID") AS BIGINT) IS NOT NULL
  AND TRY_CAST(TRIM("Date received") AS DATE) IS NOT NULL
