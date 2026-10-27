-- sql/schema.sql
-- Analytics tables for the e-commerce pipeline

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT,
    email TEXT,
    city TEXT,
    signup_date TEXT
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    unit_price REAL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product_id INTEGER,
    order_date TEXT,
    quantity INTEGER,
    unit_price REAL,
    discount_pct REAL,
    sales_amount REAL,
    order_status TEXT,
    FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
);

CREATE TABLE IF NOT EXISTS fact_web_sessions (
    session_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    session_date TEXT,
    channel TEXT,
    device TEXT,
    sessions INTEGER,
    conversions INTEGER
);

CREATE TABLE IF NOT EXISTS fact_inventory (
    product_id INTEGER,
    snapshot_date TEXT,
    stock_quantity INTEGER,
    reorder_level INTEGER,
    PRIMARY KEY (product_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS fact_search_trends (
    trend_date TEXT,
    keyword TEXT,
    search_interest INTEGER,
    source TEXT,
    PRIMARY KEY (trend_date, keyword)
);

-- Dashboard 1: Sales analytics
CREATE VIEW IF NOT EXISTS vw_sales_daily AS
SELECT
    order_date,
    COUNT(*) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(
        CASE WHEN order_status = 'COMPLETED'
             THEN sales_amount ELSE 0 END
    ), 2) AS revenue,
    SUM(CASE WHEN order_status = 'CANCELLED' THEN 1 ELSE 0 END)
        AS cancelled_orders,
    SUM(CASE WHEN order_status = 'RETURNED' THEN 1 ELSE 0 END)
        AS returned_orders
FROM fact_sales
GROUP BY order_date;

-- Dashboard 2: Customer analytics
CREATE VIEW IF NOT EXISTS vw_customer_summary AS
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    COUNT(
        CASE WHEN s.order_status = 'COMPLETED' THEN 1 END
    ) AS completed_orders,
    ROUND(SUM(
        CASE WHEN s.order_status = 'COMPLETED'
             THEN s.sales_amount ELSE 0 END
    ), 2) AS lifetime_revenue
FROM dim_customer c
LEFT JOIN fact_sales s
    ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.customer_name, c.city;

-- Dashboard 3: Product analytics
CREATE VIEW IF NOT EXISTS vw_product_summary AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(
        CASE WHEN s.order_status = 'COMPLETED' THEN 1 END
    ) AS completed_orders,
    COALESCE(SUM(
        CASE WHEN s.order_status = 'COMPLETED'
             THEN s.quantity ELSE 0 END
    ), 0) AS units_sold,
    ROUND(COALESCE(SUM(
        CASE WHEN s.order_status = 'COMPLETED'
             THEN s.sales_amount ELSE 0 END
    ), 0), 2) AS revenue
FROM dim_product p
LEFT JOIN fact_sales s
    ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.category;

-- Dashboard 4: Marketing channel performance
CREATE VIEW IF NOT EXISTS vw_channel_performance AS
SELECT
    channel,
    COUNT(*) AS total_sessions,
    SUM(conversions) AS conversions,
    ROUND(
        100.0 * SUM(conversions) / NULLIF(COUNT(*), 0),
        2
    ) AS conversion_rate_pct
FROM fact_web_sessions
GROUP BY channel;

-- Dashboard 5: Website traffic by date
CREATE VIEW IF NOT EXISTS vw_website_traffic_daily AS
SELECT
    session_date,
    device,
    SUM(sessions) AS total_sessions,
    SUM(conversions) AS total_conversions
FROM fact_web_sessions
GROUP BY session_date, device;

-- Dashboard 6: Inventory alerts
CREATE VIEW IF NOT EXISTS vw_inventory_alerts AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    i.snapshot_date,
    i.stock_quantity,
    i.reorder_level,
    CASE
        WHEN i.stock_quantity = 0 THEN 'OUT OF STOCK'
        WHEN i.stock_quantity <= i.reorder_level THEN 'LOW STOCK'
        ELSE 'IN STOCK'
    END AS stock_status
FROM fact_inventory i
JOIN dim_product p
    ON i.product_id = p.product_id;