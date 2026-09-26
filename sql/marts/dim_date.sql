-- dim_date: one row per calendar day
-- A date dimension lets every chart group by month, weekday, quarter... without
-- repeating date formulas everywhere. generate_series() creates one row per day.
CREATE OR REPLACE TABLE marts.dim_date AS
SELECT
    CAST(d AS DATE)                      AS date,
    YEAR(d)                              AS year,
    QUARTER(d)                           AS quarter,
    MONTH(d)                             AS month,
    strftime(d, '%Y-%m')                 AS year_month,
    strftime(d, '%b')                    AS month_name,
    ISODOW(d)                            AS day_of_week,     -- 1 = Monday ... 7 = Sunday
    strftime(d, '%a')                    AS day_name,
    ISODOW(d) IN (6, 7)                  AS is_weekend
FROM generate_series(DATE '2016-09-01', DATE '2018-10-31', INTERVAL 1 DAY) AS t(d);
