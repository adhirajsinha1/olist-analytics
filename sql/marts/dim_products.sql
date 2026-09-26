-- dim_products: one row per product (staging already did the cleaning)
CREATE OR REPLACE TABLE marts.dim_products AS
SELECT
    product_id,
    category,
    weight_g,
    length_cm * height_cm * width_cm AS volume_cm3,
    photos_qty
FROM staging.stg_products;
