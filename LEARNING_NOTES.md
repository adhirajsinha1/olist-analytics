# Learning Notes

Your personal study guide for this project. Everything here is something you **used**, so you can explain it in an interview.

---

## Day 1: Setup, loading data, profiling

### Tools
| Tool | What it is | Why we use it |
|---|---|---|
| **Terminal** | Text interface to your computer | Run scripts, Git, installs |
| **Git** | Version control: saves snapshots ("commits") of your project | Track history, undo mistakes, publish to GitHub |
| **GitHub** | Website that hosts Git projects | Your public portfolio |
| **Virtual environment (.venv)** | A private folder of Python packages for one project | Keeps projects from breaking each other |
| **DuckDB** | Analytics database stored in one file | Real SQL with no server to install |
| **Jupyter notebook** | Code + output + notes in one document | Exploring and explaining analysis |

### SQL learned today
| Keyword | Meaning | Example |
|---|---|---|
| `SELECT` | which columns | `SELECT order_id, order_status` |
| `FROM` | which table | `FROM raw.orders` |
| `LIMIT` | only first N rows | `LIMIT 5` |
| `WHERE` | filter **rows** | `WHERE order_status = 'delivered'` |
| `COUNT(*)` / `COUNT(col)` | count rows / count non-null values | `COUNT(*) - COUNT(col)` = nulls |
| `COUNT(DISTINCT col)` | count unique values | |
| `GROUP BY` | make groups, aggregate each | `GROUP BY order_status` |
| `HAVING` | filter **groups** (after GROUP BY) | `HAVING COUNT(*) > 1` |
| `ORDER BY ... DESC` | sort, largest first | |
| `AS` | rename a column or table | `COUNT(*) AS orders` |
| `IS NULL` | check for missing value | never `= NULL` |
| `LEFT JOIN` | keep all left rows, match right where possible | find unmatched rows |
| Subquery | a query inside brackets used by another query | |
| `MIN`, `MAX`, `AVG`, `ROUND` | aggregates / rounding | |

**SQL order of execution** (interview favourite): `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`.
That's why you can't use `WHERE` on a `COUNT()`: counting happens later, so you use `HAVING`.

### Python learned today
- `import` loads a library; `Path` builds file paths; a **dictionary** `{key: value}` maps names to values; a **for loop** repeats code for each item.
- A **DataFrame** (pandas) is a table in Python; `.plot()` makes a quick chart.

### Key concept: "grain"
The grain of a table = what **one row** represents. orders = one order, order_items = one item. Joining tables with different grains without care multiplies rows. That's the geolocation and reviews problem.

### Your-turn answers
```sql
-- 1. Sellers per state  → SP has by far the most (1,849)
SELECT seller_state, COUNT(*) AS sellers FROM raw.sellers GROUP BY seller_state ORDER BY sellers DESC;
-- 2. Average review score → 4.09
SELECT ROUND(AVG(review_score), 2) FROM raw.order_reviews;
-- 3. Orders in Nov 2017 → 7,544
SELECT COUNT(*) FROM raw.orders WHERE strftime(order_purchase_timestamp, '%Y-%m') = '2017-11';
```

### Interview questions you can now answer
**Q: Tell me about a data quality issue you found.**
A: In the Olist data, `customer_id` looked like a customer key but was actually generated per order: 99,441 IDs for 96,096 real people. Using it would have shown 0% repeat customers. I found it by comparing distinct counts and switched to `customer_unique_id`, which showed the real repeat rate is about 3%.

**Q: Why did you exclude 2016 and late 2018?**
A: Those months had only a few hundred orders against about 6,500 normally, which means incomplete data collection rather than real demand. Including them would create misleading trend drops.

**Q: WHERE vs HAVING?**
A: WHERE filters individual rows before grouping; HAVING filters groups after aggregation.

---

## Day 2: Cleaning & star schema

### Concepts
| Concept | Meaning |
|---|---|
| **Layers (raw → staging → marts)** | Never edit raw data. Staging cleans it; marts shape it for analysis. If a rule is wrong, rebuild. |
| **Star schema** | Fact tables (events + numbers) in the middle, dimension tables (descriptions) around them |
| **Fact table** | `fct_orders`, `fct_order_items`: things that happened, with measures (revenue, delivery days) |
| **Dimension table** | `dim_customers`, `dim_products`, `dim_sellers`, `dim_date`: who / what / when you slice by |
| **Grain** | What one row represents. Decide it *first* for every table. |
| **Fan-out** | Joining two "many" tables multiplies rows and inflates sums. Fix: aggregate to the target grain *before* joining. |
| **Data tests** | Queries that return rule-breaking rows; 0 rows = pass. Run on every build. |

### SQL learned today
| Keyword | Meaning |
|---|---|
| `INNER JOIN` (or `JOIN`) | keep only rows that match in both tables |
| `LEFT JOIN` | keep all left rows; right side is NULL when no match |
| `ON a.key = b.key` | the matching rule |
| `WITH name AS (...)` | CTE: a named step you can use in the next query |
| `ROW_NUMBER() OVER (PARTITION BY x ORDER BY y)` | number rows 1,2,3 within each x. Keep `= 1` to de-duplicate or pick the latest. |
| `CASE WHEN ... THEN ... ELSE ... END` | if/else to create categories |
| `COALESCE(a, b, c)` | first non-NULL value (fill missing values) |
| `CREATE OR REPLACE TABLE x AS SELECT ...` | save a query's result as a table (re-runnable) |
| `date_diff('day', a, b)` | days between two dates |
| `CAST(x AS DATE)` | convert a timestamp to a date |
| `UNION ALL` | stack results of two queries |

### Key definitions (be consistent everywhere!)
- **Revenue** = `price + freight_value` of items. Payment totals are about 1% higher because of installment interest; we use item-based revenue.
- **Late order** = delivered *date* is after the estimated delivery *date*.
- **Analysis window** = Jan 2017 – Aug 2018 (`in_analysis_window = true`).

### Your-turn answers
```sql
-- 1. Revenue by customer state → SP ≈ 5.9M, RJ ≈ 2.1M, MG ≈ 1.9M, RS, PR
SELECT customer_state, ROUND(SUM(order_revenue)) AS revenue
FROM marts.fct_orders GROUP BY customer_state ORDER BY revenue DESC NULLS LAST LIMIT 5;

-- 2. Orders per payment type → credit_card 74,975 · boleto 19,784 · voucher 3,151 · debit_card 1,527
--    (4 orders have NULL: no valid payment recorded)
SELECT main_payment_type, COUNT(*) AS orders
FROM marts.fct_orders GROUP BY main_payment_type ORDER BY orders DESC;

-- 3. Revenue by SELLER state → SP ≈ 10.2M (about 65% of all revenue!), PR, MG, RJ, SC
SELECT s.state, ROUND(SUM(f.item_revenue)) AS revenue
FROM marts.fct_order_items AS f
JOIN marts.dim_sellers AS s ON f.seller_id = s.seller_id
GROUP BY s.state ORDER BY revenue DESC LIMIT 5;
```

### Interview questions you can now answer
**Q: Walk me through your data model.**
A: Three layers. Raw holds the untouched CSVs. Staging renames columns, de-duplicates reviews with ROW_NUMBER, translates categories and removes invalid payments. Marts is a star schema with two fact tables, orders (one row per order) and order items (one row per item), plus customer, product, seller and date dimensions. Ten automated tests check uniqueness, that no rows are lost, and that revenue reconciles between the two fact tables.

**Q: What's a fan-out and how did you avoid it?**
A: When you join a table to two others that each have many rows per key, rows multiply. Joining orders to items and payments directly inflated revenue from 15.84M to 16.57M. I aggregated items and payments to one row per order in CTEs before joining, and added a reconciliation test so it can't happen silently.

**Q: INNER vs LEFT JOIN?**
A: INNER keeps only matching rows. LEFT keeps every row from the left table, with NULLs where there's no match. I used LEFT JOIN for reviews and payments so that orders without them aren't dropped.

**Q: How do you remove duplicates in SQL?**
A: `ROW_NUMBER() OVER (PARTITION BY key ORDER BY timestamp DESC)` and keep `rn = 1`. I used it to keep only the latest review per order.
