-- stg_sellers: one row per seller
CREATE OR REPLACE TABLE staging.stg_sellers AS
SELECT
    seller_id,
    seller_zip_code_prefix      AS zip_code_prefix,
    LOWER(TRIM(seller_city))    AS city,
    UPPER(TRIM(seller_state))   AS state
FROM raw.sellers;
