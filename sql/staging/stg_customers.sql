-- stg_customers: one row per customer_id (remember: customer_id is created per ORDER)
-- customer_unique_id is the real person, and we use it for every customer-level analysis.
CREATE OR REPLACE TABLE staging.stg_customers AS
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix  AS zip_code_prefix,
    LOWER(TRIM(customer_city)) AS city,
    UPPER(TRIM(customer_state)) AS state
FROM raw.customers;
