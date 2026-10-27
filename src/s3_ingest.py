
from pathlib import Path
import logging
import os
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

# Project configuration
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
LOG_DIR = PROJECT_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_DIR / ".env")

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# Log to both terminal and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            LOG_DIR / "s3_ingestion.log",
            encoding="utf-8"
        ),
    ],
)

logger = logging.getLogger(__name__)

EXPECTED_FILES = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "website_sessions.csv",
    "search_trends.csv",
    "inventory.csv",
]


def upload_file(s3_client, filename):
    """Upload one CSV and verify the stored object size."""
    local_path = RAW_DIR / filename
    object_key = f"raw/{filename}"

    if not local_path.is_file():
        raise FileNotFoundError(f"Input file missing: {local_path}")

    expected_size = local_path.stat().st_size

    logger.info("Uploading %s to s3://%s/%s",
                filename, S3_BUCKET, object_key)

    s3_client.upload_file(
        str(local_path),
        S3_BUCKET,
        object_key,
        ExtraArgs={"ContentType": "text/csv"},
    )

    # Verify the object exists and has the expected size.
    result = s3_client.head_object(
        Bucket=S3_BUCKET,
        Key=object_key,
    )

    actual_size = result["ContentLength"]

    if actual_size != expected_size:
        raise RuntimeError(
            f"Size mismatch for {filename}: "
            f"local={expected_size}, S3={actual_size}"
        )

    logger.info(
        "SUCCESS: %s | bytes=%s | s3://%s/%s",
        filename, actual_size, S3_BUCKET, object_key
    )


def main():
    if not S3_BUCKET:
        logger.error(
            "S3_BUCKET is missing. Check the .env file."
        )
        return 1

    try:
        # Uses the AWS credential chain configured on your computer.
        session = boto3.Session(region_name=AWS_REGION)
        s3_client = session.client("s3")

        # Verify access before uploading files.
        s3_client.head_bucket(Bucket=S3_BUCKET)

        failures = []

        for filename in EXPECTED_FILES:
            try:
                upload_file(s3_client, filename)
            except (
                FileNotFoundError,
                RuntimeError,
                ClientError,
                BotoCoreError,
                OSError,
            ) as exc:
                failures.append(filename)
                logger.exception(
                    "FAILED to ingest %s: %s", filename, exc
                )

        if failures:
            logger.error(
                "Ingestion finished with failures: %s",
                ", ".join(failures)
            )
            return 1

        logger.info(
            "INGESTION COMPLETED: all %s files uploaded.",
            len(EXPECTED_FILES)
        )
        return 0

    except (ClientError, BotoCoreError) as exc:
        logger.exception("AWS connection or permission error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
