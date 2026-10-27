
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from io import StringIO

from src import project_smoke_test


class TestProjectSmokeTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.raw_dir = self.root / "data" / "raw"
        self.processed_dir = self.root / "data" / "processed"

        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)

        self.config = {
            "raw_data_directory": "data/raw",
            "processed_data_directory": "data/processed",
            "required_csv_files": ["orders.csv", "customers.csv"],
            "required_processed_datasets": ["enriched_sales"],
        }

        (self.root / "project_config.json").write_text(
            json.dumps(self.config), encoding="utf-8"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_valid_files(self):
        (self.raw_dir / "orders.csv").write_text(
            "order_id\n1\n", encoding="utf-8"
        )
        (self.raw_dir / "customers.csv").write_text(
            "customer_id\n1\n", encoding="utf-8"
        )

        dataset_dir = self.processed_dir / "enriched_sales"
        dataset_dir.mkdir()

        (dataset_dir / "part-000.parquet").write_bytes(b"test")

    def run_smoke_test(self):
        with patch("sys.stdout", new_callable=StringIO):
            return project_smoke_test.main(self.root)

    def test_valid_files_pass(self):
        self.create_valid_files()
        self.assertEqual(self.run_smoke_test(), 0)

    def test_missing_csv_fails(self):
        self.create_valid_files()
        (self.raw_dir / "customers.csv").unlink()
        self.assertEqual(self.run_smoke_test(), 1)

    def test_missing_parquet_fails(self):
        self.create_valid_files()

        dataset_dir = self.processed_dir / "enriched_sales"
        for parquet_file in dataset_dir.rglob("*.parquet"):
            parquet_file.unlink()

        self.assertEqual(self.run_smoke_test(), 1)


if __name__ == "__main__":
    unittest.main()
