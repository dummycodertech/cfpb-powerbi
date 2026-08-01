{{
    config(
        materialized='table',
        description='Dimension: US states and territories with Census region classification.'
    )
}}

/*
  dim_state
  ─────────
  One row per US state/territory code. Joined from the us_states seed CSV.
  Includes Census 4-region classification (Northeast, Midwest, South, West)
  plus 'Other' for territories and APO codes that appear in CFPB data.

  States with NULL or blank codes in the fact layer will join as NULL;
  they are not dropped from dim_state.
*/

SELECT
    state_code,
    state_name,
    region
FROM {{ ref('us_states') }}
