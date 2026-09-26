-- Revenue must be identical whether summed per item or per order (catches join fan-out).
SELECT items_total, orders_total FROM (
    SELECT (SELECT ROUND(SUM(item_revenue), 2) FROM marts.fct_order_items) AS items_total,
           (SELECT ROUND(SUM(order_revenue), 2) FROM marts.fct_orders)     AS orders_total
) WHERE items_total <> orders_total;
