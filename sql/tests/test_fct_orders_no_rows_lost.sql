-- Every raw order must reach fct_orders (joins must not drop orders). Returns a row if counts differ.
SELECT (SELECT COUNT(*) FROM raw.orders) AS raw_rows, (SELECT COUNT(*) FROM marts.fct_orders) AS fct_rows
WHERE (SELECT COUNT(*) FROM raw.orders) <> (SELECT COUNT(*) FROM marts.fct_orders);
