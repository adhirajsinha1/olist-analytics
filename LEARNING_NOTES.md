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

---

## Day 3: Revenue, growth & payments

### Window functions: `FUNCTION() OVER (...)`
A normal aggregate with GROUP BY **collapses** rows. A window function calculates across rows but **keeps every row**.

| Pattern | What it does |
|---|---|
| `LAG(x) OVER (ORDER BY month)` | previous row's value → month-over-month growth: `x / LAG(x) - 1` |
| `LEAD(x) OVER (ORDER BY month)` | next row's value |
| `SUM(x) OVER (ORDER BY month)` | running (cumulative) total |
| `AVG(x) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` | 3-month moving average |
| `SUM(x) OVER ()` | grand total on every row → share: `x / SUM(x) OVER ()` |
| `RANK() OVER (ORDER BY x DESC)` | rank (ties share a rank, then skip: 1,1,3) |
| `DENSE_RANK()` | ties share a rank, no skip: 1,1,2 |
| `ROW_NUMBER()` | always unique: 1,2,3 |
| `... OVER (PARTITION BY group ORDER BY ...)` | restart the calculation for each group |

**Interview favourite:** *"Find the top 3 products in each category"* →
`ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC)` then keep `<= 3`.

### Other SQL today
- `CREATE TEMP VIEW name AS SELECT ...`: a saved query that behaves like a table (avoids repeating filters)
- `SUM(CASE WHEN condition THEN x END)`: **conditional aggregation**, e.g. revenue for 2017 and 2018 as two columns in one query
- `strftime(date, '%Y-%m')`, `YEAR()`, `MONTH()`, `QUARTER()`, `ISODOW()`, `HOUR()`: date parts

### pandas learned today
| Code | Meaning |
|---|---|
| `df["col"]` | one column |
| `df.iloc[0]` | first row |
| `df[df["orders"] > 100]` | filter rows |
| `df["col"].mean()`, `.sum()`, `.idxmax()` | summary / position of the max |
| `df["col"].pct_change()` | % change vs previous row (pandas' LAG) |
| `df.pivot(index=, columns=, values=)` | reshape long → grid (for heatmaps) |
| `df.head(10)` | first 10 rows |

### Chart principles used
- **One chart = one message**, written as the title ("plateau in 2018", not "Revenue chart")
- Highlight what matters (Black Friday bar in orange), grey for context
- **Never two y-axes.** Two measures of different scale go in two charts side by side.
- Sequential data (heatmap) uses **one colour** from light to dark

### Your-turn answers
```sql
-- 1. Revenue by year & quarter → biggest: 2018 Q2 (≈ R$ 3.32M), then 2018 Q1 (≈ R$ 3.23M)
SELECT YEAR(order_date) AS year, QUARTER(order_date) AS quarter, ROUND(SUM(order_revenue)) AS revenue
FROM orders GROUP BY year, quarter ORDER BY year, quarter;

-- 2. MoM growth in number of orders
WITH m AS (SELECT strftime(order_date, '%Y-%m') AS month, COUNT(*) AS orders FROM orders GROUP BY month)
SELECT month, orders,
       ROUND(100.0 * (orders / LAG(orders) OVER (ORDER BY month) - 1), 1) AS mom_growth_pct
FROM m ORDER BY month;
-- careful: orders is an integer, so use 100.0 (not 100) to force decimal division!

-- 3. Top 5 sellers → the #1 seller made ≈ R$ 249k
SELECT RANK() OVER (ORDER BY SUM(item_revenue) DESC) AS rank, seller_id, ROUND(SUM(item_revenue)) AS revenue
FROM marts.fct_order_items
WHERE order_date BETWEEN '2017-01-01' AND '2018-08-31' AND order_status NOT IN ('canceled', 'unavailable')
GROUP BY seller_id ORDER BY rank LIMIT 5;
```

### Interview questions you can now answer
**Q: What's the difference between a window function and GROUP BY?**
A: GROUP BY collapses rows into one per group. A window function computes across a set of rows but keeps every row, so I can show each month's revenue next to the previous month's (LAG) or a running total.

**Q: How did you calculate month-over-month growth?**
A: Aggregate revenue by month in a CTE, then `revenue / LAG(revenue) OVER (ORDER BY month) - 1`.

**Q: What were the main revenue insights?**
A: Jan–Aug revenue grew about 140% year over year, but monthly revenue has been flat at around R$ 1.0–1.15M throughout 2018. Order volume grew about 8× while average order value stayed at around R$ 160, so growth came entirely from volume. That points to AOV levers: installments (7+ installment orders have about 3× the AOV), bundles and free-shipping thresholds. Black Friday reached about 7.5× normal daily orders, which has logistics implications.

**Q: Why compare Jan–Aug 2018 with Jan–Aug 2017 instead of full years?**
A: 2018 data ends in August. Comparing the same months keeps the comparison fair and removes seasonality effects like Black Friday.

---

## Day 4: Customers, retention, cohorts & RFM

### Concepts
| Concept | Meaning |
|---|---|
| **Repeat rate** | % of customers with 2+ orders |
| **Cohort** | Customers grouped by the month of their *first* purchase |
| **Cohort retention** | % of a cohort that buys again N months after their first purchase. Separates retention from acquisition. |
| **RFM** | Recency (days since last order), Frequency (number of orders), Monetary (total spend) → segments marketing can act on |
| **Self-join** | Joining a table to itself (e.g. 1st order vs 2nd order of the same customer) |
| **Long vs wide data** | Long = one row per cohort×month; wide = grid. `pivot` converts long → wide. |

### SQL learned today
| Code | Meaning |
|---|---|
| `date_trunc('month', ts)` | round a timestamp down to the 1st of its month |
| `date_diff('month', a, b)` | whole months between two dates |
| `NTILE(5) OVER (ORDER BY x)` | split rows into 5 equal groups (quintiles), labelled 1–5 |
| `AVG(CASE WHEN cond THEN 1 ELSE 0 END)` | share of rows meeting a condition (a rate) |
| `ts + INTERVAL 180 DAY` | date arithmetic |
| `COUNT(DISTINCT CASE WHEN ... THEN id END)` | count unique ids that meet a condition |

### pandas learned today
- `df.pivot(index="cohort", columns="month_number", values="customers")` → cohort grid
- `grid.div(grid[0], axis=0)` → divide each row by its first column (turn counts into %)
- `df.groupby("col")["x"].agg(["count", "min", "max", "mean"])` → summary per group
- `series.median()`, `(series == 0).sum()` → median; count of rows matching a condition

### The "sanity check your metric" story (use this in interviews!)
The headline repeat rate was 3.0%, but 30% of those "second orders" were placed **the same day** as the first, probably split baskets across sellers.
Excluding them, the **true repeat rate is about 2.1%**. Lesson: before reporting a metric, check whether it measures what you think it measures.

### Your-turn answers
```sql
-- 1. Customers with 3+ orders → 252
SELECT COUNT(*) FROM marts.dim_customers WHERE total_orders >= 3;

-- 2. Avg recency & spend by r_score → recency falls from ~473 days (score 1) to ~48 days (score 5);
--    spend is ~R$ 157–170 in every group, so recency and spend are unrelated here
SELECT r_score, ROUND(AVG(recency_days)) AS avg_recency, ROUND(AVG(monetary), 1) AS avg_spend
FROM marts.customer_rfm GROUP BY r_score ORDER BY r_score;

-- 3. Spending quartiles → Q1: R$ 10–63 · Q2: 63–108 · Q3: 108–183 · Q4: 183–13,664
SELECT quartile, MIN(monetary) AS min_spend, MAX(monetary) AS max_spend
FROM (SELECT monetary, NTILE(4) OVER (ORDER BY monetary) AS quartile FROM marts.customer_rfm)
GROUP BY quartile ORDER BY quartile;
```

### Interview questions you can now answer
**Q: How would you measure customer retention?**
A: Cohort analysis. Group customers by first-purchase month, then calculate the % of each cohort that purchases again in each following month. At Olist, every cohort had under 1% monthly retention, and only about 2% returned within 6 months, so low retention is structural rather than a one-off.

**Q: Explain RFM and how you adapted it.**
A: RFM scores customers on recency, frequency and monetary value. Normally each is split into quintiles, but 97% of Olist customers bought once, so frequency had no spread. I scored recency and monetary with NTILE(5), treated frequency as one vs two-plus orders, and mapped the combinations to seven named segments with a recommended action each.

**Q: What did you recommend?**
A: Two segments, new big spenders and at-risk big spenders, are about 30% of customers but 56% of revenue, so CRM spend should go there first, including a win-back campaign for the 14k at-risk big spenders. I also recommended timing post-purchase journeys at 60–90 days (the median genuine repeat is 75 days), focusing on home and fashion buyers who repeat 2–3× more, and fixing late first deliveries, since those customers return about 20% less often.

**Q: What's NTILE vs RANK?**
A: RANK gives each row its position (1, 2, 3… with ties). NTILE(n) divides the ordered rows into n equal-sized buckets and returns the bucket number, which makes it good for quintiles and deciles.

---

## Day 5: Delivery, sellers & statistical testing

### Hypothesis testing in one paragraph
Start with a **null hypothesis (H₀)**: "no difference / no relationship". The test computes a **p-value**, the probability of seeing a difference at least this big **if H₀ were true**.
If p < α (usually **0.05**), the result is unlikely under H₀, so we **reject H₀** and call it *statistically significant*.

**Common traps (interviewers test these):**
- The p-value is **not** the probability that H₀ is true.
- "Significant" ≠ "important". With huge samples, tiny differences become significant, so **always report the effect size** (difference in means, % change, Cohen's d).
- **Correlation ≠ causation.** To prove cause you need a controlled experiment (A/B test).
- Not rejecting H₀ ≠ proving there's no difference (you may just lack data).

### Which test when?
| Question | Data | Test | scipy |
|---|---|---|---|
| Do two groups have different **means**? | numeric | **Welch's t-test** | `stats.ttest_ind(a, b, equal_var=False)` |
| Same, but data is ordinal/skewed | ranks | **Mann-Whitney U** | `stats.mannwhitneyu(a, b)` |
| Are two **categorical** variables related? | counts in a table | **Chi-square** | `stats.chi2_contingency(table)` |
| Do two variables move together? | numeric/ordinal | **Pearson** (linear) / **Spearman** (rank) correlation | `stats.pearsonr`, `stats.spearmanr` |
| More than two groups' means? | numeric | ANOVA | `stats.f_oneway(a, b, c)` |

**Cohen's d** = (mean₁ − mean₂) / pooled SD → 0.2 small, 0.5 medium, 0.8+ large.

### pandas learned today
- `pd.crosstab(df.a, df.b)` → counts table (input for chi-square)
- `df[df.is_late]` / `df[~df.is_late]` → filter by a True/False column (`~` means NOT)

### Your-turn answers
```sql
-- 1. By payment type → boleto: 7.3% late & 13.4 days vs credit card 6.7% & 12.3 days.
--    Boleto takes ~1 day longer (the slip has to clear before the order is approved); reviews are the same (4.16)
SELECT main_payment_type, COUNT(*) AS orders,
       ROUND(100 * AVG(CAST(is_late AS INT)), 1) AS late_pct,
       ROUND(AVG(review_score), 2) AS avg_review, ROUND(AVG(delivery_days), 1) AS avg_days
FROM delivered GROUP BY main_payment_type ORDER BY orders DESC;

-- 3. Underperforming sellers by state → SP (37), PR (4), MG (3). But SP also has most sellers overall,
--    so compare RATES, not counts, before concluding anything!
SELECT seller_state, COUNT(*) FROM marts.seller_scorecard
WHERE performance_flag = 'Underperforming' GROUP BY seller_state ORDER BY 2 DESC;
```
```python
# 2. t-test on order value → late R$ 176 vs on-time R$ 159, p ≈ 1e-8
d = sql("SELECT is_late, order_revenue FROM delivered")
late, on_time = d[d.is_late].order_revenue, d[~d.is_late].order_revenue
print(late.mean(), on_time.mean(), stats.ttest_ind(late, on_time, equal_var=False))
# Lesson: statistically significant (tiny p) but a SMALL practical difference (~R$ 17).
# Bigger orders are slightly more likely to be late (maybe bulky items / more sellers).
```

### Interview questions you can now answer
**Q: What is a p-value?**
A: The probability of seeing a result at least as extreme as the one observed if the null hypothesis were true. Below 0.05, we reject the null. It isn't the probability that the null is true, and it says nothing about how big the effect is.

**Q: How did you show lateness affects satisfaction?**
A: Late orders average 2.27★ vs 4.29★ on time. Welch's t-test gave p≈0 with Cohen's d of 1.47, a very large effect, and Mann-Whitney agreed since reviews are ordinal. The drop starts from just 1–3 days late (3.3★), so what matters is meeting the promised date rather than raw speed.

**Q: Did you find anything about retention?**
A: Customers whose first delivery was late had a 2.54% repeat rate vs 3.12%, about a 19% relative drop. A chi-square test gave p≈0.01, so it's significant. It's an association rather than proven causation, and confirming causation would need an experiment.

**Q: What would you do about delivery?**
A: The carrier leg is about 75% of delivery time, and late rates spiked to 12–19% after demand jumps, so the priorities are carrier capacity planning before peaks and route fixes for the North-East and Rio de Janeiro. Estimates are padded by about 12 days, so tightening them could lift conversion. For sellers, I built a scorecard: 50 established sellers underperform, including the #2 seller by revenue, and handling time correlates with lateness, which makes it a good SLA metric.

**Q: Statistical vs practical significance?**
A: Late orders were about R$17 more expensive on average, with p≈1e-8, which is significant but practically small. With large samples, almost everything is significant, so I always pair a p-value with an effect size.
