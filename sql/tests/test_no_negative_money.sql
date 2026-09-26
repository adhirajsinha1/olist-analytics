-- Prices and freight can't be negative. Returns offending items.
SELECT order_id, price, freight_value FROM marts.fct_order_items WHERE price < 0 OR freight_value < 0;
