
import csv
from pathlib import Path
from collections import Counter

PROJECT_DIR = Path(__file__).resolve().parent.parent
HISTORY_FILE = PROJECT_DIR / "logs" / "pipeline_history.csv"


def main():
    if not HISTORY_FILE.exists():
        print(f"ERROR: Execution history not found: {HISTORY_FILE}")
        return 1

    with HISTORY_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        runs = list(reader)

    if not runs:
        print("No pipeline executions recorded yet.")
        return 0

    latest = runs[-1]
    statuses = Counter(
        row.get("status", "").strip().upper() for row in runs
    )

    print("=" * 45)
    print("E-COMMERCE PIPELINE MONITOR")
    print("=" * 45)
    print(f"Total recorded runs : {len(runs)}")
    print(f"Successful runs     : {statuses['SUCCESS']}")
    print(f"Failed runs         : {statuses['FAILED']}")
    print("-" * 45)
    print(f"Latest start time   : {latest.get('start_time', '')}")
    print(f"Latest end time     : {latest.get('end_time', '')}")
    print(f"Latest status       : {latest.get('status', '')}")
    print(f"Latest duration     : {latest.get('duration_seconds', '')} seconds")
    print(f"Latest error        : {latest.get('error', '') or 'None'}")
    print("=" * 45)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
