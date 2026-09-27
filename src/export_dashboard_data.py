"""
STEP 3 OF THE PIPELINE: export small, dashboard-ready files.

The full DuckDB database is large and not committed to GitHub, so the online
dashboard can't use it. Instead we export only the columns the dashboard needs
as compressed Parquet files (a fast, compact column-based format) into
dashboard/data/. These ARE committed, so Streamlit Cloud can read them.

Run after build_models.py:
    python src/export_dashboard_data.py
"""
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "olist.duckdb"
OUT_DIR = PROJECT_ROOT / "dashboard" / "data"

EXPORTS = {
    # one row per valid order in the analysis window
    # (customer ids are replaced by small integers: smaller files, no raw ids published)
    "orders": """
        SELECT DENSE_RANK() OVER (ORDER BY customer_unique_id) AS customer_key,
               customer_state, order_status, order_date,
               ROUND(order_revenue, 2) AS order_revenue, item_count,
               main_payment_type, installments,
               delivery_days, days_vs_estimate, is_late, review_score,
               customer_order_number
        FROM marts.fct_orders
        WHERE in_analysis_window AND order_status NOT IN ('canceled', 'unavailable')
    """,
    # one row per item sold, with its category and the seller's state
    "items": """
        SELECT f.order_date, c.state AS customer_state, p.category,
               s.state AS seller_state, ROUND(f.item_revenue, 2) AS item_revenue
        FROM marts.fct_order_items f
        JOIN marts.dim_products  p ON f.product_id = p.product_id
        JOIN marts.dim_sellers   s ON f.seller_id = s.seller_id
        JOIN marts.dim_customers c ON f.customer_unique_id = c.customer_unique_id
        WHERE f.order_date BETWEEN '2017-01-01' AND '2018-08-31'
          AND f.order_status NOT IN ('canceled', 'unavailable')
    """,
    "rfm": """
        SELECT r.segment, r.recency_days, r.frequency, r.monetary, r.r_score, r.m_score,
               c.state AS customer_state
        FROM marts.customer_rfm r
        JOIN marts.dim_customers c ON r.customer_unique_id = c.customer_unique_id
    """,
    "sellers": """
        SELECT LEFT(seller_id, 8) AS seller, seller_state, orders, revenue, avg_review,
               late_rate, avg_handling_days, revenue_rank, performance_flag
        FROM marts.seller_scorecard
    """,
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    for name, query in EXPORTS.items():
        out = OUT_DIR / f"{name}.parquet"
        con.execute(f"COPY ({query}) TO '{out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        rows = con.execute(f"SELECT COUNT(*) FROM '{out.as_posix()}'").fetchone()[0]
        print(f"  ✔ {out.relative_to(PROJECT_ROOT)}  {rows:>7,} rows  {out.stat().st_size / 1e6:.1f} MB")
    con.close()


if __name__ == "__main__":
    main()
