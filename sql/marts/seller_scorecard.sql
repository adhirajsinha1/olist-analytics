-- seller_scorecard: one row per seller with performance KPIs and a flag
-- Only orders in the analysis window that weren't canceled/unavailable.
--
-- Flag rules (agreed business thresholds; tweak as needed):
--   'Low volume'       fewer than 30 orders, too few to judge fairly
--   'Underperforming'  late rate above 15% OR average review below 3.5
--   'Good'             everyone else
CREATE OR REPLACE TABLE marts.seller_scorecard AS
WITH seller_orders AS (
    -- one row per seller × order (a seller can have several items in the same order)
    SELECT
        i.seller_id,
        i.order_id,
        SUM(i.item_revenue)                                       AS revenue,
        MAX(o.review_score)                                       AS review_score,
        MAX(CAST(o.is_late AS INTEGER))                           AS is_late,
        MAX(date_diff('hour', o.approved_at, o.shipped_at)) / 24.0 AS handling_days
    FROM marts.fct_order_items AS i
    JOIN marts.fct_orders      AS o ON i.order_id = o.order_id
    WHERE o.in_analysis_window
      AND o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY i.seller_id, i.order_id
),
kpis AS (
    SELECT
        seller_id,
        COUNT(*)                          AS orders,
        ROUND(SUM(revenue), 2)            AS revenue,
        ROUND(AVG(review_score), 2)       AS avg_review,
        ROUND(AVG(is_late), 3)            AS late_rate,          -- share of delivered orders that were late
        ROUND(AVG(handling_days), 1)      AS avg_handling_days   -- approval → handed to carrier
    FROM seller_orders
    GROUP BY seller_id
)
SELECT
    k.seller_id,
    s.state                                          AS seller_state,
    k.orders,
    k.revenue,
    k.avg_review,
    k.late_rate,
    k.avg_handling_days,
    RANK() OVER (ORDER BY k.revenue DESC)            AS revenue_rank,
    CASE
        WHEN k.orders < 30                                  THEN 'Low volume'
        WHEN k.late_rate > 0.15 OR k.avg_review < 3.5       THEN 'Underperforming'
        ELSE                                                     'Good'
    END                                              AS performance_flag
FROM kpis k
JOIN marts.dim_sellers s ON k.seller_id = s.seller_id;
