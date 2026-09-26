-- fct_orders: one row per order (grain = order_id). The main table for most analysis.
--
-- Problem: items, payments and reviews each have their OWN grain (many rows per order).
-- If we joined them all directly to orders, rows would multiply (an order with 3 items
-- and 2 payments would become 6 rows!). Solution: first squash each one to ONE row
-- per order in a CTE, THEN join. Always aggregate to the target grain before joining.
CREATE OR REPLACE TABLE marts.fct_orders AS
WITH items AS (
    SELECT
        order_id,
        COUNT(*)                   AS item_count,
        COUNT(DISTINCT seller_id)  AS seller_count,
        SUM(price)                 AS items_value,
        SUM(freight_value)         AS freight_value
    FROM staging.stg_order_items
    GROUP BY order_id
),
payments_ranked AS (
    SELECT
        order_id,
        payment_type,
        payment_value,
        payment_installments,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_value DESC) AS rn
    FROM staging.stg_payments
),
payments AS (
    SELECT
        order_id,
        SUM(payment_value)                          AS payment_value,
        MAX(payment_installments)                   AS installments,
        MAX(CASE WHEN rn = 1 THEN payment_type END) AS main_payment_type  -- type that paid the most
    FROM payments_ranked
    GROUP BY order_id
)
SELECT
    -- keys
    o.order_id,
    c.customer_unique_id,
    c.state                                          AS customer_state,

    -- status & dates
    o.order_status,
    o.purchased_at,
    CAST(o.purchased_at AS DATE)                     AS order_date,
    o.approved_at,
    o.shipped_at,
    o.delivered_at,
    o.estimated_delivery_at,

    -- which order is this for the customer? 1 = first purchase, 2 = second...
    ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.purchased_at) AS customer_order_number,

    -- money (item-based revenue: price + freight)
    COALESCE(i.item_count, 0)                        AS item_count,
    i.seller_count,
    i.items_value,
    i.freight_value,
    i.items_value + i.freight_value                  AS order_revenue,
    p.payment_value,
    p.main_payment_type,
    p.installments,

    -- delivery metrics: only meaningful for delivered orders that have a delivery date
    CASE WHEN o.order_status = 'delivered' AND o.delivered_at IS NOT NULL
         THEN date_diff('day', o.purchased_at, o.delivered_at) END                    AS delivery_days,
    CASE WHEN o.order_status = 'delivered' AND o.delivered_at IS NOT NULL
         THEN date_diff('day', CAST(o.estimated_delivery_at AS DATE), CAST(o.delivered_at AS DATE)) END
                                                                                      AS days_vs_estimate,  -- positive = late
    CASE WHEN o.order_status = 'delivered' AND o.delivered_at IS NOT NULL
         THEN CAST(o.delivered_at AS DATE) > CAST(o.estimated_delivery_at AS DATE) END AS is_late,

    -- customer satisfaction
    r.review_score,

    -- flag for the 20 complete months we analyse (data quality issue #1)
    o.purchased_at >= TIMESTAMP '2017-01-01' AND o.purchased_at < TIMESTAMP '2018-09-01' AS in_analysis_window

FROM staging.stg_orders         AS o
JOIN staging.stg_customers      AS c ON o.customer_id = c.customer_id
LEFT JOIN items                 AS i ON o.order_id = i.order_id
LEFT JOIN payments              AS p ON o.order_id = p.order_id
LEFT JOIN staging.stg_reviews   AS r ON o.order_id = r.order_id;
