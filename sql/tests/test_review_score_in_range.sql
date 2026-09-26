-- Review scores must be 1-5. Returns invalid rows.
SELECT order_id, review_score FROM marts.fct_orders WHERE review_score NOT BETWEEN 1 AND 5;
