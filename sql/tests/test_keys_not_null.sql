-- Key columns must never be empty. Returns offending rows.
SELECT order_id FROM marts.fct_orders WHERE order_id IS NULL OR customer_unique_id IS NULL
UNION ALL
SELECT order_id FROM marts.fct_order_items WHERE product_id IS NULL OR seller_id IS NULL;
