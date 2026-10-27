
from pathlib import Path
import json
import sys


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config" / "project_config.json"


def main(project_dir=None):
    root = Path(project_dir) if project_dir else PROJECT_DIR
    config_file = root / "config" / "project_config.json"

    if project_dir is not None:
        # Support isolated test directories.
        config_file = root / "project_config.json"

    if not config_file.is_file():
        print(f"FAIL: Configuration file not found: {config_file}")
        return 1

    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: Cannot read configuration: {exc}")
        return 1

    raw_dir = root / config["raw_data_directory"]
    processed_dir = root / config["processed_data_directory"]
    failures = []

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
        return 1

    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
