-- stg_orders: one row per order
-- Cleaning: rename the long timestamp columns to short, consistent names.
-- Nothing is filtered out here; staging keeps every row, and later layers decide what to use.
CREATE OR REPLACE TABLE staging.stg_orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp       AS purchased_at,
    order_approved_at              AS approved_at,
    order_delivered_carrier_date   AS shipped_at,
    order_delivered_customer_date  AS delivered_at,
    order_estimated_delivery_date  AS estimated_delivery_at
FROM raw.orders;
