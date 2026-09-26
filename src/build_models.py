"""
STEP 2 OF THE PIPELINE: turn raw tables into clean, analysis-ready tables.

    raw.*      (untouched CSV data, built by load_data.py)
      ↓  sql/staging/*.sql   rename, clean, de-duplicate
    staging.*
      ↓  sql/marts/*.sql     star schema: fact + dimension tables
    marts.*
      ↓  sql/tests/*.sql     automated data quality checks

How to run (from the project folder, with .venv active):
    python src/build_models.py
"""

from pathlib import Path
import sys
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
DB_PATH = PROJECT_ROOT / "data" / "olist.duckdb"

# Marts are listed explicitly so the build order is clear (dimensions, then facts).
MART_ORDER = [
    "dim_date",
    "dim_customers",
    "dim_products",
    "dim_sellers",
    "fct_order_items",
    "fct_orders",
]


def run_sql_file(con, path):
    """Run one .sql file and print the row count of the table it created."""
    con.execute(path.read_text())
    table = f"{path.parent.name}.{path.stem}"          # e.g. staging.stg_orders
    rows = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  ✔ {table:<32} {rows:>9,} rows")


def run_tests(con):
    """
    Each test file is a query that returns the rows that BREAK a rule.
    0 rows returned = test passed. This is the same idea dbt uses.
    """
    failures = 0
    for path in sorted((SQL_DIR / "tests").glob("*.sql")):
        bad_rows = con.execute(path.read_text()).fetchall()
        if bad_rows:
            failures += 1
            print(f"  ✘ FAIL  {path.stem}  ({len(bad_rows)} bad rows, e.g. {bad_rows[0]})")
        else:
            print(f"  ✔ pass  {path.stem}")
    return failures


def main():
    if not DB_PATH.exists():
        sys.exit("Database not found. Run `python src/load_data.py` first.")

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS staging")
    con.execute("CREATE SCHEMA IF NOT EXISTS marts")

    print("\n1) Building staging tables")
    for path in sorted((SQL_DIR / "staging").glob("*.sql")):
        run_sql_file(con, path)

    print("\n2) Building star schema (marts)")
    for name in MART_ORDER:
        run_sql_file(con, SQL_DIR / "marts" / f"{name}.sql")

    print("\n3) Running data tests")
    failures = run_tests(con)
    con.close()

    if failures:
        sys.exit(f"\n{failures} test(s) failed. Fix before analysing!")
    print("\nAll tests passed. Data is ready for analysis.")


if __name__ == "__main__":
    main()
