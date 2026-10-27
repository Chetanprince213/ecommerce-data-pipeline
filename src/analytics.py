
from pathlib import Path
import duckdb

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"

# Connect to a local DuckDB database
DB_PATH = PROJECT_DIR / "ecommerce_analytics.duckdb"
con = duckdb.connect(str(DB_PATH))

datasets = {
    "enriched_sales": DATA_DIR / "enriched_sales",
    "daily_sales": DATA_DIR / "daily_sales",
    "customer_summary": DATA_DIR / "customer_summary",
    "product_summary": DATA_DIR / "product_summary",
}

# Register each Parquet dataset as a SQL view
for name, folder in datasets.items():
    files = list(folder.rglob("*.parquet"))

    if not files:
        raise FileNotFoundError(
            f"No Parquet files found in {folder}. "
            "Download the dataset from S3 first."
        )

    # DuckDB reads all matching Parquet files, including nested partitions.
    parquet_glob = (folder / "**" / "*.parquet").as_posix()
    con.execute(
        f"CREATE OR REPLACE VIEW {name} AS "
        f"SELECT * FROM read_parquet('{parquet_glob}')"
    )

    count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"{name}: {count} rows")

print("\n--- TOTAL SALES ---")
print(
    con.execute("""
        SELECT
            COUNT(DISTINCT order_id) AS total_orders,
            ROUND(SUM(sales_amount), 2) AS total_sales
        FROM enriched_sales
    """).fetchdf()
)

print("\n--- DAILY SALES ---")
print(
    con.execute("""
        SELECT
            order_date,
            order_status,
            order_count,
            ROUND(total_sales, 2) AS total_sales
        FROM daily_sales
        ORDER BY order_date DESC
        LIMIT 10
    """).fetchdf()
)

print("\n--- TOP 10 PRODUCTS ---")
print(
    con.execute("""
        SELECT
            product_id,
            product_name,
            units_sold,
            ROUND(total_sales, 2) AS total_sales
        FROM product_summary
        ORDER BY total_sales DESC
        LIMIT 10
    """).fetchdf()
)

print("\n--- TOP 10 CUSTOMERS BY SALES ---")
print(
    con.execute("""
        SELECT
            customer_id,
            order_count,
            ROUND(total_sales, 2) AS total_sales
        FROM customer_summary
        ORDER BY total_sales DESC
        LIMIT 10
    """).fetchdf()
)

con.close()
print("\nAnalytics completed successfully.")
