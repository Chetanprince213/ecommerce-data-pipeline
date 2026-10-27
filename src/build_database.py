
from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
SQL_DIR = PROJECT_DIR / "sql"
DB_PATH = PROJECT_DIR / "data" / "ecommerce.db"
SCHEMA_PATH = SQL_DIR / "schema.sql"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

FILES = {
    "customers": "customers.csv",
    "products": "products.csv",
    "orders": "orders.csv",
    "website_sessions": "website_sessions.csv",
    "search_trends": "search_trends.csv",
    "inventory": "inventory.csv",
}


def main():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        # Enable foreign key checks in SQLite.
        conn.execute("PRAGMA foreign_keys = ON")

        # 1. Load the CSVs into raw tables.
        for table_name, filename in FILES.items():
            csv_path = RAW_DIR / filename

            if not csv_path.exists():
                raise FileNotFoundError(
                    f"Required input file not found: {csv_path}"
                )

            df = pd.read_csv(csv_path)
            df.to_sql(
                f"raw_{table_name}",
                conn,
                if_exists="replace",
                index=False
            )
            print(f"Loaded raw_{table_name}: {len(df)} rows")

        # 2. Create the analytics schema and views.
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)

        # 3. Rebuild the analytics tables on every run.
        # This makes the demo repeatable and avoids duplicate rows.
        for table in [
            "fact_sales",
            "fact_web_sessions",
            "fact_inventory",
            "fact_search_trends",
            "dim_customer",
            "dim_product",
        ]:
            conn.execute(f"DELETE FROM {table}")

        # 4. Populate customer and product dimensions.
        conn.execute("""
            INSERT INTO dim_customer
            SELECT
                customer_id,
                customer_name,
                email,
                city,
                signup_date
            FROM raw_customers
        """)

        conn.execute("""
            INSERT INTO dim_product
            SELECT
                product_id,
                product_name,
                category,
                unit_price
            FROM raw_products
        """)

        # 5. Populate sales fact table.
        conn.execute("""
            INSERT INTO fact_sales
            SELECT
                order_id,
                customer_id,
                product_id,
                order_date,
                quantity,
                unit_price,
                discount_pct,
                sales_amount,
                order_status
            FROM raw_orders
        """)

        # 6. Populate web sessions fact table.
        conn.execute("""
            INSERT INTO fact_web_sessions
            SELECT
                session_id,
                customer_id,
                session_date,
                channel,
                device,
                sessions,
                conversions
            FROM raw_website_sessions
        """)

        # 7. Populate inventory and search-trend facts.
        conn.execute("""
            INSERT INTO fact_inventory
            SELECT
                product_id,
                snapshot_date,
                stock_quantity,
                reorder_level
            FROM raw_inventory
        """)

        conn.execute("""
            INSERT INTO fact_search_trends
            SELECT
                trend_date,
                keyword,
                search_interest,
                source
            FROM raw_search_trends
        """)

        # 8. Display a quick pipeline summary.
        print("\n--- ANALYTICS TABLE COUNTS ---")

        for table in [
            "dim_customer",
            "dim_product",
            "fact_sales",
            "fact_web_sessions",
            "fact_inventory",
            "fact_search_trends",
        ]:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count} rows")

        # 9. Display key dashboard metrics.
        metrics = conn.execute("""
            SELECT
                COUNT(*) AS order_records,
                ROUND(SUM(
                    CASE WHEN order_status = 'COMPLETED'
                         THEN sales_amount ELSE 0 END
                ), 2) AS completed_revenue,
                SUM(CASE WHEN order_status = 'COMPLETED'
                         THEN 1 ELSE 0 END) AS completed_orders
            FROM fact_sales
        """).fetchone()

        print("\n--- SALES SUMMARY ---")
        print(f"Order records: {metrics[0]}")
        print(f"Completed revenue: {metrics[1]}")
        print(f"Completed orders: {metrics[2]}")

    print(f"\nDatabase successfully built: {DB_PATH}")


if __name__ == "__main__":
    main()
