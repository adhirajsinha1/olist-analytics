# Data Quality Report

**Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle): 9 tables, ~1.45M rows in total
**Method:** SQL profiling in DuckDB, see [`notebooks/01_data_profiling.ipynb`](../notebooks/01_data_profiling.ipynb)

## Tables loaded
| Table | Rows | Grain (one row = …) |
|---|---:|---|
| orders | 99,441 | one order |
| order_items | 112,650 | one item within an order |
| order_payments | 103,886 | one payment for an order (orders can be split across payments) |
| order_reviews | 99,224 | one review |
| customers | 99,441 | one order's customer record (see issue 2) |
| products | 32,951 | one product |
| sellers | 3,095 | one seller |
| geolocation | 1,000,163 | one lat/lng point for a zip prefix |
| category_translation | 71 | one category (Portuguese → English) |

## Issues found and how each is handled
| # | Issue | Evidence | Impact if ignored | Decision |
|---|---|---|---|---|
| 1 | Incomplete edge periods | 329 orders in all of 2016; only 20 orders in Sep–Oct 2018 (vs ~6,500/month normally) | Trend charts show false drops | Restrict time-series analysis to **Jan 2017 – Aug 2018** |
| 2 | `customer_id` is generated per order | 99,441 customer_ids vs **96,096** customer_unique_ids | Repeat-purchase rate would appear to be 0% | Use `customer_unique_id` to identify people |
| 3 | Duplicate reviews | 547 orders have more than one review; 814 repeated review_id rows | Orders double-counted when joining reviews | Keep the latest review per order |
| 4 | Geolocation has ~53 rows per zip prefix | 1,000,163 rows / 19,015 prefixes | Joins multiply rows ~50× | Analyse geography at state level; average coordinates per prefix if mapping |
| 5 | Delivered orders with no delivery date | 8 orders | Undefined delivery time | Exclude from delivery metrics |
| 6 | Missing / untranslated categories | 610 products with no category; 2 categories missing from translation table | Gaps in category analysis | Label `unknown`; translate `pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos` manually |
| 7 | Orders without items | 775 orders, almost all `unavailable` / `canceled` | None for revenue | Naturally excluded from item-level revenue |
| 8 | Undefined payment type | 3 payments with `not_defined` | Noise | Exclude |

## Early business signals
- **97.0%** of orders were delivered; 1.2% canceled or unavailable.
- Only **3.1%** of customers (2,997 of 96,096) ordered more than once, so **retention is the key problem to investigate**.
- Order volume spikes in **November 2017** (7,544 orders, Black Friday).
- Credit card accounts for ~74% of payments, boleto for ~19%.
