
from pathlib import Path
import csv
import subprocess
import sys
import time
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"
HISTORY_FILE = LOG_DIR / "pipeline_history.csv"


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


def run_task(task_name, script_path):
    log(f"STARTED: {task_name}")

    result = subprocess.run(
        [PYTHON, str(PROJECT_DIR / script_path)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.stdout:
        log(result.stdout.strip())

    if result.stderr:
        log(result.stderr.strip())

    if result.returncode != 0:
        log(f"FAILED: {task_name}, exit code {result.returncode}")
        raise RuntimeError(f"{task_name} failed")

    log(f"SUCCEEDED: {task_name}")


def save_history(start_time, end_time, duration, status, error):
    file_exists = HISTORY_FILE.exists()

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists or HISTORY_FILE.stat().st_size == 0:
            writer.writerow([
                "start_time",
                "end_time",
                "duration_seconds",
                "status",
                "error",
            ])

        writer.writerow([
            start_time,
            end_time,
            round(duration, 2),
            status,
            error,
        ])


def main():
    start_clock = time.perf_counter()
    start_time = datetime.now().astimezone().isoformat(timespec="seconds")
    status = "SUCCESS"
    error = ""

    log("=" * 50)
    log("E-COMMERCE PIPELINE STARTED")

    tasks = [
         ("Analytics", "src/analytics.py"),
        ("Data quality checks", "src/data_quality.py"),
     ]
    
#     tasks = [
#     ("Failure test", "src/this_file_does_not_exist.py"),
# ]

    try:
        for task_name, script_path in tasks:
            run_task(task_name, script_path)

        log("PIPELINE COMPLETED SUCCESSFULLY")

    except Exception as exc:
        status = "FAILED"
        error = str(exc)
        log(f"PIPELINE FAILED: {error}")

    finally:
        duration = time.perf_counter() - start_clock
        end_time = datetime.now().astimezone().isoformat(timespec="seconds")

        save_history(
            start_time,
            end_time,
            duration,
            status,
            error,
        )

        log(f"Pipeline status: {status}")
        log(f"Duration: {duration:.2f} seconds")
        log(f"Execution history: {HISTORY_FILE}")

    if status == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
