-- One row per real customer. Returns duplicates.
SELECT customer_unique_id, COUNT(*) AS n FROM marts.dim_customers GROUP BY customer_unique_id HAVING COUNT(*) > 1;
