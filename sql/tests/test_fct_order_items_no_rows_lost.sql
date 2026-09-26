-- Every raw item must reach fct_order_items. Returns a row if counts differ.
SELECT (SELECT COUNT(*) FROM raw.order_items) AS raw_rows, (SELECT COUNT(*) FROM marts.fct_order_items) AS fct_rows
WHERE (SELECT COUNT(*) FROM raw.order_items) <> (SELECT COUNT(*) FROM marts.fct_order_items);
