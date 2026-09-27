-- Every customer in the RFM table has exactly one row and a segment. Returns problems.
SELECT customer_unique_id, COUNT(*) AS n
FROM marts.customer_rfm
GROUP BY customer_unique_id
HAVING COUNT(*) > 1 OR MAX(CASE WHEN segment IS NULL THEN 1 ELSE 0 END) = 1;
