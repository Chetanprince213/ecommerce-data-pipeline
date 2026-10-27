
import json
import unittest
from pathlib import Path

from src import project_smoke_test


class TestProjectSmokeTest(unittest.TestCase):

    def test_configuration_file_exists(self):
        self.assertTrue(project_smoke_test.CONFIG_FILE.is_file())

    def test_required_file_list(self):
        config = json.loads(
            project_smoke_test.CONFIG_FILE.read_text(encoding="utf-8")
        )

        self.assertIn("orders.csv", config["required_csv_files"])
        self.assertIn("customers.csv", config["required_csv_files"])
        self.assertEqual(len(config["required_csv_files"]), 6)

    def test_required_datasets(self):
        config = json.loads(
            project_smoke_test.CONFIG_FILE.read_text(encoding="utf-8")
        )

        expected = {
            "enriched_sales",
            "daily_sales",
            "customer_summary",
            "product_summary",
        }

        self.assertEqual(
            set(config["required_processed_datasets"]),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
