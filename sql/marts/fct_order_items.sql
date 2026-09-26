-- fct_order_items: one row per item sold (grain = order + item number)
-- Used for product, category and seller analysis.
-- Revenue definition used across the project: item revenue = price + freight.
CREATE OR REPLACE TABLE marts.fct_order_items AS
SELECT
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    c.customer_unique_id,
    o.order_status,
    o.purchased_at,
    CAST(o.purchased_at AS DATE)    AS order_date,
    i.price,
    i.freight_value,
    i.price + i.freight_value       AS item_revenue
FROM staging.stg_order_items AS i
JOIN staging.stg_orders      AS o ON i.order_id = o.order_id
JOIN staging.stg_customers   AS c ON o.customer_id = c.customer_id;
