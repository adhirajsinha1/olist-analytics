-- stg_products: one row per product
-- Cleaning (data quality issue #6):
--   * translate categories to English with a LEFT JOIN (keeps products with no match)
--   * manually translate the 2 categories missing from the translation table
--   * label products with no category as 'unknown'
--   * fix the misspelled column names ("lenght")
CREATE OR REPLACE TABLE staging.stg_products AS
SELECT
    p.product_id,
    COALESCE(                          -- COALESCE = take the first value that isn't NULL
        t.product_category_name_english,
        CASE p.product_category_name
            WHEN 'pc_gamer' THEN 'pc_gamer'
            WHEN 'portateis_cozinha_e_preparadores_de_alimentos' THEN 'portable_kitchen_and_food_preparers'
        END,
        'unknown'
    )                                  AS category,
    p.product_name_lenght              AS name_length,
    p.product_description_lenght       AS description_length,
    p.product_photos_qty               AS photos_qty,
    p.product_weight_g                 AS weight_g,
    p.product_length_cm                AS length_cm,
    p.product_height_cm                AS height_cm,
    p.product_width_cm                 AS width_cm
FROM raw.products AS p
LEFT JOIN raw.category_translation AS t
       ON p.product_category_name = t.product_category_name;
