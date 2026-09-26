-- stg_payments: one row per payment (an order can be paid with several, e.g. card + voucher)
-- Cleaning: drop the 3 payments with payment_type = 'not_defined' (data quality issue #8).
CREATE OR REPLACE TABLE staging.stg_payments AS
SELECT
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
FROM raw.order_payments
WHERE payment_type <> 'not_defined';
