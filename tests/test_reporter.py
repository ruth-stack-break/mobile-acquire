import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.reporter import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    def test_row_counting_and_database_fetching(self):
        reporter = ReportGenerator("templates")
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE calls (number TEXT, date INTEGER, "
                "duration INTEGER, type INTEGER)"
            )
            cursor.execute(
                "INSERT INTO calls VALUES ('123456', 1700000000000, 30, 1)"
            )
            conn.commit()
            conn.close()

            count = reporter.get_sqlite_row_count(db_path, "calls")
            self.assertEqual(count, 1)

            calls = reporter.get_call_logs(db_path)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]['number'], '123456')

    def test_report_generation(self):
        reporter = ReportGenerator("templates")
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            device_info = {
                "model": "test_model",
                "manufacturer": "test_man",
                "android_version": "11",
                "sdk_version": "30",
                "serial": "123456",
                "brand": "test_brand",
                "device_name": "test_device",
                "device_time": "Tue May 26 12:00:00 UTC 2026"
            }
            with open(
                output_dir / "device_info.json",
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(device_info, f)

            manifest = {"device_info.json": "hash123"}
            report_path = reporter.generate(
                output_dir,
                "CASE-001",
                "Investigator One",
                manifest
            )

            self.assertTrue(report_path.exists())
            self.assertTrue((output_dir / "report.json").exists())
