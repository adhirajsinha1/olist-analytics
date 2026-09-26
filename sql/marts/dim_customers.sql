-- dim_customers: one row per REAL customer (customer_unique_id)
--
-- Uses two CTEs (WITH ... AS): named mini-queries that we build step by step,
-- like variables in a program. Much easier to read than nested subqueries.
CREATE OR REPLACE TABLE marts.dim_customers AS
WITH customer_orders AS (
    -- Step 1: attach the real person (customer_unique_id) to every order
    SELECT
        c.customer_unique_id,
        c.city,
        c.state,
        o.order_id,
        o.purchased_at
    FROM staging.stg_orders    AS o
    JOIN staging.stg_customers AS c ON o.customer_id = c.customer_id
),
latest_location AS (
    -- Step 2: a customer may move, so take the city/state from their most recent order
    SELECT customer_unique_id, city, state
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchased_at DESC) AS rn
        FROM customer_orders
    )
    WHERE rn = 1
)
-- Step 3: one row per customer with their order history summarised
SELECT
    co.customer_unique_id,
    l.city,
    l.state,
    MIN(co.purchased_at)         AS first_order_at,
    MAX(co.purchased_at)         AS last_order_at,
    COUNT(DISTINCT co.order_id)  AS total_orders,
    COUNT(DISTINCT co.order_id) > 1 AS is_repeat_customer
FROM customer_orders AS co
JOIN latest_location AS l ON co.customer_unique_id = l.customer_unique_id
GROUP BY co.customer_unique_id, l.city, l.state;
