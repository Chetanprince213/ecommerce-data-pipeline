
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
REPORT_DIR = PROJECT_DIR / "data" / "processed"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Required columns in each dataset
REQUIRED_COLUMNS = {
    "customers.csv": [
        "customer_id", "customer_name", "email", "city", "signup_date"
    ],
    "products.csv": [
        "product_id", "product_name", "category", "unit_price"
    ],
    "orders.csv": [
        "order_id", "customer_id", "product_id", "order_date",
        "quantity", "unit_price", "discount_pct", "sales_amount",
        "order_status"
    ],
    "website_sessions.csv": [
        "session_id", "customer_id", "session_date", "channel",
        "device", "sessions", "conversions"
    ],
    "search_trends.csv": [
        "trend_date", "keyword", "search_interest", "source"
    ],
    "inventory.csv": [
        "product_id", "snapshot_date", "stock_quantity", "reorder_level"
    ],
}

issues = []
report_lines = []


def check(condition, message):
    """Record a failed data-quality rule."""
    if not condition:
        issues.append(message)


def load_csv(filename):
    path = RAW_DIR / filename

    if not path.exists():
        issues.append(f"MISSING FILE: {filename}")
        return None

    df = pd.read_csv(path)

    missing_columns = set(REQUIRED_COLUMNS[filename]) - set(df.columns)

    if missing_columns:
        issues.append(
            f"{filename}: missing columns {sorted(missing_columns)}"
        )
        return None

    report_lines.append(
        f"{filename}: {len(df)} rows, {len(df.columns)} columns"
    )
    return df


def check_unique(df, column, filename):
    duplicate_count = int(df[column].duplicated().sum())
    check(
        duplicate_count == 0,
        f"{filename}: {duplicate_count} duplicate values in {column}"
    )


def check_no_nulls(df, columns, filename):
    for column in columns:
        null_count = int(df[column].isna().sum())
        check(
            null_count == 0,
            f"{filename}: {null_count} null values in {column}"
        )


# 1. Load all files
data = {
    filename: load_csv(filename)
    for filename in REQUIRED_COLUMNS
}

# Stop further checks if any file is missing or malformed.
if any(df is None for df in data.values()):
    report_lines.extend(["", "STATUS: FAILED"])
else:
    customers = data["customers.csv"]
    products = data["products.csv"]
    orders = data["orders.csv"]
    sessions = data["website_sessions.csv"]
    trends = data["search_trends.csv"]
    inventory = data["inventory.csv"]

    # 2. Required fields must not be empty
    check_no_nulls(
        customers,
        ["customer_id", "email"],
        "customers.csv"
    )
    check_no_nulls(
        products,
        ["product_id", "product_name", "unit_price"],
        "products.csv"
    )
    check_no_nulls(
        orders,
        [
            "order_id", "customer_id", "product_id",
            "order_date", "quantity", "sales_amount"
        ],
        "orders.csv"
    )
    check_no_nulls(
        sessions,
        ["session_id", "customer_id", "session_date"],
        "website_sessions.csv"
    )

    # 3. Primary keys must be unique
    check_unique(customers, "customer_id", "customers.csv")
    check_unique(products, "product_id", "products.csv")
    check_unique(orders, "order_id", "orders.csv")
    check_unique(sessions, "session_id", "website_sessions.csv")

    # 4. Numeric business rules
    check((products["unit_price"] < 0).sum() == 0,
          "products.csv: negative unit prices found")

    check((orders["quantity"] <= 0).sum() == 0,
          "orders.csv: quantity must be positive")

    check((orders["unit_price"] < 0).sum() == 0,
          "orders.csv: negative unit prices found")

    check(
        (~orders["discount_pct"].between(0, 100)).sum() == 0,
        "orders.csv: discount_pct must be between 0 and 100"
    )

    check((orders["sales_amount"] < 0).sum() == 0,
          "orders.csv: negative sales amounts found")

    check(
        (~sessions["conversions"].isin([0, 1])).sum() == 0,
        "website_sessions.csv: conversions must be 0 or 1"
    )

    check((trends["search_interest"] < 0).sum() == 0,
          "search_trends.csv: negative search interest found")

    check((inventory["stock_quantity"] < 0).sum() == 0,
          "inventory.csv: negative stock quantity found")

    # 5. Referential integrity: IDs must exist in their parent datasets
    customer_ids = set(customers["customer_id"])
    product_ids = set(products["product_id"])

    invalid_order_customers = ~orders["customer_id"].isin(customer_ids)
    invalid_order_products = ~orders["product_id"].isin(product_ids)
    invalid_session_customers = ~sessions["customer_id"].isin(customer_ids)
    invalid_inventory_products = ~inventory["product_id"].isin(product_ids)

    check(
        invalid_order_customers.sum() == 0,
        "orders.csv: customer_id values not found in customers.csv"
    )
    check(
        invalid_order_products.sum() == 0,
        "orders.csv: product_id values not found in products.csv"
    )
    check(
        invalid_session_customers.sum() == 0,
        "website_sessions.csv: unknown customer_id values"
    )
    check(
        invalid_inventory_products.sum() == 0,
        "inventory.csv: unknown product_id values"
    )

    # 6. Date fields must be parseable
    date_columns = {
        "customers.csv": ("signup_date", customers),
        "orders.csv": ("order_date", orders),
        "website_sessions.csv": ("session_date", sessions),
        "search_trends.csv": ("trend_date", trends),
        "inventory.csv": ("snapshot_date", inventory),
    }

    for filename, (column, df) in date_columns.items():
        parsed = pd.to_datetime(df[column], errors="coerce")
        bad_dates = int(parsed.isna().sum())
        check(
            bad_dates == 0,
            f"{filename}: {bad_dates} invalid dates in {column}"
        )

    # 7. Summarize data
    report_lines.extend([
        "",
        f"Total customers: {len(customers)}",
        f"Total products: {len(products)}",
        f"Total order records: {len(orders)}",
        f"Total website sessions: {len(sessions)}",
        f"Total trend records: {len(trends)}",
        f"Total inventory records: {len(inventory)}",
    ])

report_lines.append("")
report_lines.append("STATUS: FAILED" if issues else "STATUS: PASSED")

if issues:
    report_lines.append("")
    report_lines.append("ISSUES:")
    report_lines.extend(f"- {issue}" for issue in issues)

# Save the report
report_path = REPORT_DIR / "data_quality_report.txt"
report_path.write_text("\n".join(report_lines), encoding="utf-8")

print("\n".join(report_lines))
print(f"\nReport saved to: {report_path}")

if issues:
    raise SystemExit("Data quality checks failed. Review the report.")
