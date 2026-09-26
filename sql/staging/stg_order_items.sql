-- stg_order_items: one row per item in an order
-- An order with 3 items has 3 rows here (order_item_id = 1, 2, 3).
CREATE OR REPLACE TABLE staging.stg_order_items AS
SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date  AS shipping_limit_at,
    price,
    freight_value
FROM raw.order_items;
