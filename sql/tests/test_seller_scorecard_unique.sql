-- One row per seller in the scorecard. Returns duplicates.
SELECT seller_id, COUNT(*) AS n FROM marts.seller_scorecard GROUP BY seller_id HAVING COUNT(*) > 1;
