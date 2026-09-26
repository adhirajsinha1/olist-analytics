-- fct_orders must have exactly one row per order. Returns duplicated order_ids (should be none).
SELECT order_id, COUNT(*) AS n FROM marts.fct_orders GROUP BY order_id HAVING COUNT(*) > 1;
