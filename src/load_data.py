"""
STEP 1 OF THE PIPELINE: load the 9 raw Olist CSV files into a DuckDB database.

What is DuckDB?  A database that lives in a single file on your computer
(data/olist.duckdb). No server to install - perfect for analytics projects.

How to run (from the project folder, with the virtual environment active):
    python src/load_data.py
"""

from pathlib import Path   # Path makes file paths work on Mac, Windows and Linux
import duckdb              # the database library

# --- 1. Where things live ------------------------------------------------------
# __file__ is this script. .parent.parent goes up two folders to the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "data" / "olist.duckdb"

# --- 2. Which CSV becomes which table -----------------------------------------
# A Python "dictionary": short table name -> CSV file name
TABLES = {
    "customers":            "olist_customers_dataset.csv",
    "geolocation":          "olist_geolocation_dataset.csv",
    "order_items":          "olist_order_items_dataset.csv",
    "order_payments":       "olist_order_payments_dataset.csv",
    "order_reviews":        "olist_order_reviews_dataset.csv",
    "orders":               "olist_orders_dataset.csv",
    "products":             "olist_products_dataset.csv",
    "sellers":              "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def main():
    # Open (or create) the database file
    con = duckdb.connect(str(DB_PATH))

    # A "schema" is a folder inside the database. We keep untouched source data
    # in a schema called "raw" - later we'll build clean tables in other schemas.
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    print(f"Loading CSVs from {RAW_DIR}\n")
    for table_name, file_name in TABLES.items():
        csv_path = RAW_DIR / file_name
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing file: {csv_path}  (did you unzip the Kaggle data into data/raw?)")

        # read_csv_auto looks at the file and guesses column names and types
        # (text, number, timestamp...). CREATE OR REPLACE lets us re-run safely.
        safe_path = str(csv_path).replace("'", "''")
        con.execute(f"""
            CREATE OR REPLACE TABLE raw.{table_name} AS
            SELECT * FROM read_csv_auto('{safe_path}', header = true)
        """)

        # Quick sanity check: how many rows and columns did we load?
        rows = con.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
        cols = len(con.execute(f"DESCRIBE raw.{table_name}").fetchall())
        print(f"  raw.{table_name:<22} {rows:>9,} rows   {cols:>2} columns")

    con.close()
    print(f"\nDone! Database saved to {DB_PATH}")


# This line means: only run main() when the file is run directly
if __name__ == "__main__":
    main()
