-- dim_sellers: one row per seller
CREATE OR REPLACE TABLE marts.dim_sellers AS
SELECT seller_id, city, state
FROM staging.stg_sellers;
