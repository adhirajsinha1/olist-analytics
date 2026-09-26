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
