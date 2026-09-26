-- stg_reviews: ONE row per order (the raw table has duplicates, data quality issue #3)
--
-- How: ROW_NUMBER() numbers the reviews of each order (PARTITION BY order_id),
-- newest first (ORDER BY ... DESC). Then we keep only number 1 = the latest review.
-- This "ROW_NUMBER + keep 1" pattern is THE standard way to de-duplicate in SQL.
CREATE OR REPLACE TABLE staging.stg_reviews AS
WITH numbered AS (
    SELECT
        order_id,
        review_id,
        review_score,
        review_comment_message,
        review_creation_date     AS review_created_at,
        review_answer_timestamp  AS review_answered_at,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY review_answer_timestamp DESC
        ) AS rn
    FROM raw.order_reviews
)
SELECT
    order_id,
    review_id,
    review_score,
    review_comment_message,
    review_created_at,
    review_answered_at
FROM numbered
WHERE rn = 1;
