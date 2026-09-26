-- After cleaning, every product has a category (at least 'unknown'). Returns products without one.
SELECT product_id FROM marts.dim_products WHERE category IS NULL;
