-- After de-duplication each order has at most one review. Returns orders that still have several.
SELECT order_id, COUNT(*) AS n FROM staging.stg_reviews GROUP BY order_id HAVING COUNT(*) > 1;
