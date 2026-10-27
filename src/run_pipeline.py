
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

TASKS = [
    ("Project smoke test", "src/project_smoke_test.py"),
    ("Analytics", "src/analytics.py"),
    ("Data quality checks", "src/data_quality.py"),
    # ("Pipeline monitor", "src/pipeline_monitor.py"),
]


def log(message):
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


def run_task(task_name, script_path):
    full_path = PROJECT_DIR / script_path

    log(f"STARTED: {task_name}")

    if not full_path.is_file():
        raise RuntimeError(f"{task_name}: script not found: {full_path}")

    try:
        result = subprocess.run(
            [PYTHON, str(full_path)],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(
            f"{task_name}: could not start script: {exc}"
        ) from exc

    if result.stdout:
        log(result.stdout.rstrip())

    if result.stderr:
        log(f"STDERR ({task_name}):\n{result.stderr.rstrip()}")

    if result.returncode != 0:
        raise RuntimeError(
            f"{task_name} failed with exit code {result.returncode}"
        )

    log(f"SUCCEEDED: {task_name}")


def save_history(start_time, end_time, duration, status, error):
    file_exists = HISTORY_FILE.exists()

    with HISTORY_FILE.open(
        "a", newline="", encoding="utf-8"
    ) as file:
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

    try:
        for task_name, script_path in TASKS:
            run_task(task_name, script_path)

        log("PIPELINE COMPLETED SUCCESSFULLY")

    except Exception as exc:
        status = "FAILED"
        error = f"{type(exc).__name__}: {exc}"
        log(f"PIPELINE FAILED: {error}")

    finally:
        duration = time.perf_counter() - start_clock
        end_time = datetime.now().astimezone().isoformat(timespec="seconds")

        try:
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

        except OSError as exc:
            log(f"CRITICAL: Could not save execution history: {exc}")
            status = "FAILED"

    try:
        run_task("Pipeline monitor", "src/pipeline_monitor.py")
    except Exception as exc:
        log(f"WARNING: Pipeline monitor failed: {exc}")

    if status == "FAILED":
        raise SystemExit(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
