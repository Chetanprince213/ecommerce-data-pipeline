
from pathlib import Path
from datetime import datetime, timezone

import duckdb
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports" / "data_quality"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = PROJECT_DIR / "ecommerce_analytics.duckdb"

if not DB_PATH.exists():
    raise FileNotFoundError(
        "DuckDB database not found. Run python src/analytics.py first."
    )

con = duckdb.connect(str(DB_PATH), read_only=True)
results = []


def run_check(check_name, sql, expected=0):
    actual = con.execute(sql).fetchone()[0]
    passed = actual == expected

    results.append({
        "check_name": check_name,
        "expected_value": expected,
        "actual_value": actual,
        "status": "PASS" if passed else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    })

    print(
        f"[{'PASS' if passed else 'FAIL'}] {check_name}: "
        f"expected={expected}, actual={actual}"
    )


# 1. Verify that all four processed datasets have Parquet files.
for dataset in [
    "enriched_sales",
    "daily_sales",
    "customer_summary",
    "product_summary",
]:
    files = list((DATA_DIR / dataset).rglob("*.parquet"))

    results.append({
        "check_name": f"{dataset}_files_exist",
        "expected_value": "> 0",
        "actual_value": len(files),
        "status": "PASS" if len(files) > 0 else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    })

    print(
        f"[{'PASS' if files else 'FAIL'}] "
        f"{dataset} Parquet files: {len(files)}"
    )


# 2. Check required order fields.
run_check(
    "Missing order IDs",
    "SELECT COUNT(*) FROM enriched_sales WHERE order_id IS NULL",
)

run_check(
    "Missing customer IDs",
    "SELECT COUNT(*) FROM enriched_sales WHERE customer_id IS NULL",
)

run_check(
    "Missing product IDs",
    "SELECT COUNT(*) FROM enriched_sales WHERE product_id IS NULL",
)

# 3. Check duplicate orders.
run_check(
    "Duplicate order IDs",
    """
    SELECT COUNT(*)
    FROM (
        SELECT order_id
        FROM enriched_sales
        GROUP BY order_id
        HAVING COUNT(*) > 1
    ) duplicates
    """,
)

# 4. Check invalid quantities and prices.
run_check(
    "Invalid quantities",
    """
    SELECT COUNT(*)
    FROM enriched_sales
    WHERE quantity IS NULL OR quantity <= 0
    """,
)

run_check(
    "Invalid prices or discounts",
    """
    SELECT COUNT(*)
    FROM enriched_sales
    WHERE unit_price IS NULL
       OR unit_price < 0
       OR discount_pct IS NULL
       OR discount_pct < 0
       OR discount_pct > 100
    """,
)

# 5. Check calculated sales amounts.
run_check(
    "Sales amount mismatches",
    """
    SELECT COUNT(*)
    FROM enriched_sales
    WHERE sales_amount_matches = FALSE
       OR sales_amount_matches IS NULL
    """,
)

# 6. Check that the main dataset contains records.
enriched_count = con.execute(
    "SELECT COUNT(*) FROM enriched_sales"
).fetchone()[0]

results.append({
    "check_name": "Enriched sales dataset is not empty",
    "expected_value": "> 0",
    "actual_value": enriched_count,
    "status": "PASS" if enriched_count > 0 else "FAIL",
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
})

print(
    f"[{'PASS' if enriched_count > 0 else 'FAIL'}] "
    f"Enriched sales dataset is not empty: {enriched_count} rows"
)

con.close()

# Save the complete quality report.
report = pd.DataFrame(results)
csv_path = REPORT_DIR / "data_quality_report.csv"
report.to_csv(csv_path, index=False)

failed = int((report["status"] == "FAIL").sum())

summary_path = REPORT_DIR / "data_quality_summary.txt"
with open(summary_path, "w", encoding="utf-8") as file:
    file.write("E-COMMERCE DATA QUALITY REPORT\n")
    file.write("=" * 35 + "\n")
    file.write(f"Total checks: {len(report)}\n")
    file.write(f"Passed checks: {len(report) - failed}\n")
    file.write(f"Failed checks: {failed}\n")
    file.write(
        f"Overall status: {'PASS' if failed == 0 else 'FAIL'}\n"
    )

print("\nReport saved:", csv_path)
print("Summary saved:", summary_path)
print(f"Passed: {len(report) - failed}")
print(f"Failed: {failed}")
print("Overall status:", "PASS" if failed == 0 else "FAIL")
