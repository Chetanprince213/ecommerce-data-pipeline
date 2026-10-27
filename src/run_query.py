
from pathlib import Path
import sqlite3

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_DIR / "data" / "ecommerce.db"

queries = {
    "TOP 5 PRODUCTS BY REVENUE": """
        SELECT product_name, category, units_sold, revenue
        FROM vw_product_summary
        ORDER BY revenue DESC
        LIMIT 5
    """,
    "TOP 5 CUSTOMERS BY REVENUE": """
        SELECT customer_id, customer_name, city,
               completed_orders, lifetime_revenue
        FROM vw_customer_summary
        ORDER BY lifetime_revenue DESC
        LIMIT 5
    """,
    "REVENUE BY ORDER DATE (LATEST 10 DAYS)": """
        SELECT order_date, total_orders, units_sold, revenue
        FROM vw_sales_daily
        ORDER BY order_date DESC
        LIMIT 10
    """,
    "MARKETING CHANNEL PERFORMANCE": """
        SELECT channel, total_sessions, conversions,
               conversion_rate_pct
        FROM vw_channel_performance
        ORDER BY conversions DESC
    """,
    "LOW-STOCK PRODUCTS": """
        SELECT product_name, stock_quantity, reorder_level,
               stock_status
        FROM vw_inventory_alerts
        WHERE stock_status != 'IN STOCK'
    """
}

with sqlite3.connect(DB_PATH) as conn:
    for title, query in queries.items():
        print(f"\n--- {title} ---")
        cursor = conn.execute(query)
        columns = [item[0] for item in cursor.description]
        print(" | ".join(columns))

        for row in cursor.fetchall():
            print(" | ".join(str(value) for value in row))
