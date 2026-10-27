
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

REQUIRED_CSV_FILES = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "website_sessions.csv",
    "search_trends.csv",
    "inventory.csv",
]

REQUIRED_DATASETS = [
    "enriched_sales",
    "daily_sales",
    "customer_summary",
    "product_summary",
]


def main():
    failures = []

    print("=" * 55)
    print("E-COMMERCE PROJECT SMOKE TEST")
    print("=" * 55)

    print("\nChecking raw CSV files...")

    for filename in REQUIRED_CSV_FILES:
        path = RAW_DIR / filename

        if path.is_file() and path.stat().st_size > 0:
            print(f"PASS: {filename}")
        else:
            print(f"FAIL: {filename} is missing or empty")
            failures.append(str(path))

    print("\nChecking processed Parquet datasets...")

    for dataset in REQUIRED_DATASETS:
        dataset_dir = PROCESSED_DIR / dataset

        parquet_files = (
            list(dataset_dir.rglob("*.parquet"))
            if dataset_dir.is_dir()
            else []
        )

        if parquet_files:
            print(
                f"PASS: {dataset} "
                f"({len(parquet_files)} Parquet file(s))"
            )
        else:
            print(f"FAIL: {dataset} has no Parquet files")
            failures.append(str(dataset_dir))

    print("\n" + "=" * 55)

    if failures:
        print(f"RESULT: FAILED ({len(failures)} check(s))")
        print("Review the missing files or dataset folders above.")
        sys.exit(1)

    print("RESULT: ALL CHECKS PASSED")
    print("Required raw and processed files are present.")


if __name__ == "__main__":
    main()
