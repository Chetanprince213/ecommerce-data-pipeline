
from pathlib import Path
import json
import sys

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config" / "project_config.json"


def main():
    failures = []

    if not CONFIG_FILE.is_file():
        print(f"FAIL: Configuration file not found: {CONFIG_FILE}")
        sys.exit(1)

    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: Cannot read configuration: {exc}")
        sys.exit(1)

    raw_dir = PROJECT_DIR / config["raw_data_directory"]
    processed_dir = PROJECT_DIR / config["processed_data_directory"]

    print("=" * 55)
    print("E-COMMERCE PROJECT SMOKE TEST")
    print("=" * 55)

    print("\nChecking raw CSV files...")

    for filename in config["required_csv_files"]:
        path = raw_dir / filename

        if path.is_file() and path.stat().st_size > 0:
            print(f"PASS: {filename}")
        else:
            print(f"FAIL: {filename} is missing or empty")
            failures.append(str(path))

    print("\nChecking processed Parquet datasets...")

    for dataset in config["required_processed_datasets"]:
        dataset_dir = processed_dir / dataset

        parquet_files = (
            list(dataset_dir.rglob("*.parquet"))
            if dataset_dir.is_dir()
            else []
        )

        if parquet_files:
            print(f"PASS: {dataset} ({len(parquet_files)} Parquet file(s))")
        else:
            print(f"FAIL: {dataset} has no Parquet files")
            failures.append(str(dataset_dir))

    print("\n" + "=" * 55)

    if failures:
        print(f"RESULT: FAILED ({len(failures)} check(s))")
        print("Review the missing files or dataset folders above.")
        sys.exit(1)

    print("RESULT: ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
