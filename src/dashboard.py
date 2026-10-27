
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "ecommerce_analytics.duckdb"

st.set_page_config(
    page_title="E-commerce Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("E-commerce Sales Analytics")
st.caption("Data processed with AWS Glue and queried locally using DuckDB")

if not DB_PATH.exists():
    st.error("DuckDB database not found. Run python src/analytics.py first.")
    st.stop()

try:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    sales = con.execute("""
        SELECT
            COUNT(DISTINCT order_id) AS total_orders,
            ROUND(COALESCE(SUM(sales_amount), 0), 2) AS total_sales
        FROM enriched_sales
    """).fetchdf()

    daily = con.execute("""
        SELECT
            order_date,
            order_status,
            order_count,
            total_sales,
            units_sold
        FROM daily_sales
        ORDER BY order_date
    """).fetchdf()

    products = con.execute("""
        SELECT
            product_id,
            product_name,
            units_sold,
            total_sales,
            order_count
        FROM product_summary
        ORDER BY total_sales DESC
    """).fetchdf()

    customers = con.execute("""
        SELECT
            customer_id,
            order_count,
            total_sales,
            distinct_products
        FROM customer_summary
        ORDER BY total_sales DESC
    """).fetchdf()

    con.close()

except Exception as error:
    st.error(f"Could not load analytics data: {error}")
    st.info("Run python src/analytics.py first and check for errors.")
    st.stop()

# Summary metrics
col1, col2, col3 = st.columns(3)

col1.metric("Total Sales", f"{sales.iloc[0]['total_sales']:,.2f}")
col2.metric("Total Orders", f"{int(sales.iloc[0]['total_orders']):,}")
col3.metric("Products", f"{products['product_id'].nunique():,}")

st.divider()

# Daily sales trend
st.subheader("Daily Sales Trend")

daily["order_date"] = pd.to_datetime(daily["order_date"])
daily_trend = (
    daily.groupby("order_date", as_index=False)["total_sales"]
    .sum()
    .sort_values("order_date")
)

if not daily_trend.empty:
    st.line_chart(
        daily_trend.set_index("order_date")["total_sales"],
        y_label="Sales",
    )
else:
    st.info("No daily sales data is available.")

# Product and customer analysis
left, right = st.columns(2)

with left:
    st.subheader("Top 10 Products by Sales")
    top_products = products.head(10).sort_values("total_sales")
    if not top_products.empty:
        st.bar_chart(
            top_products.set_index("product_name")["total_sales"],
            x_label="Product",
            y_label="Sales",
        )
    st.dataframe(products.head(10), use_container_width=True)

with right:
    st.subheader("Top 10 Customers by Sales")
    st.dataframe(customers.head(10), use_container_width=True)

st.subheader("Daily Sales Details")
st.dataframe(daily.tail(20), use_container_width=True)

st.caption("Portfolio project: synthetic e-commerce data, AWS S3, AWS Glue, PySpark, DuckDB and Streamlit.")
