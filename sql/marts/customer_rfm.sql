-- customer_rfm: one row per customer with RFM scores and a marketing segment
--
-- RFM = Recency (how recently they bought), Frequency (how often), Monetary (how much).
-- Reference date = 2018-09-01, the day after our analysis window ends.
--
-- Why not the textbook 5x5x5 RFM? 97% of Olist customers bought only once, so
-- frequency has no spread to split into 5 groups. We score Recency and Monetary with
-- NTILE(5) (quintiles: 1 = worst 20%, 5 = best 20%) and treat Frequency as 1 vs 2+.
CREATE OR REPLACE TABLE marts.customer_rfm AS
WITH base AS (
    SELECT
        customer_unique_id,
        date_diff('day', MAX(purchased_at), TIMESTAMP '2018-09-01') AS recency_days,
        COUNT(*)                                                    AS frequency,
        SUM(order_revenue)                                          AS monetary
    FROM marts.fct_orders
    WHERE in_analysis_window
      AND order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_unique_id
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,   -- most recent buyers get 5
           NTILE(5) OVER (ORDER BY monetary ASC)      AS m_score    -- biggest spenders get 5
    FROM base
)
SELECT
    customer_unique_id,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary,
    r_score,
    m_score,
    CASE
        WHEN frequency >= 2 AND r_score >= 4 THEN 'Champions'
        WHEN frequency >= 2                  THEN 'Loyal (lapsing)'
        WHEN r_score >= 4 AND m_score >= 4   THEN 'New big spenders'
        WHEN r_score >= 4                    THEN 'New customers'
        WHEN r_score <= 2 AND m_score >= 4   THEN 'At risk: big spenders'
        WHEN r_score <= 2                    THEN 'Lost / one-off'
        ELSE                                      'Needs attention'
    END AS segment
FROM scored;
