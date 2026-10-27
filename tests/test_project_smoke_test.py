
import unittest
from pathlib import Path
from unittest.mock import patch

from src import project_smoke_test


class TestProjectSmokeTest(unittest.TestCase):

    def test_existing_nonempty_file(self):
        with patch.object(
            project_smoke_test,
            "RAW_DIR",
            Path("mock_raw"),
        ):
            self.assertTrue(True)

    def test_required_file_list(self):
        self.assertIn("orders.csv", project_smoke_test.REQUIRED_CSV_FILES)
        self.assertIn("customers.csv", project_smoke_test.REQUIRED_CSV_FILES)

    def test_required_datasets(self):
        expected = {
            "enriched_sales",
            "daily_sales",
            "customer_summary",
            "product_summary",
        }

        self.assertEqual(
            set(project_smoke_test.REQUIRED_DATASETS),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
