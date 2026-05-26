import unittest
from src.parser import DumpsysPackageParser


class TestDumpsysPackageParser(unittest.TestCase):
    def test_parse_valid_output(self):
        sample_output = """
Activity Resolver Table:
  Full MIME Types:
      multipart/related:
        ee8c053 com.android.chrome/com.google.android.apps.chrome.IntentDispatcher
Packages:
  Package [com.android.chrome] (653e88d):
    userId=10123
    pkg=Package{8e8f810 com.android.chrome}
    versionName=83.0.4103.106
    firstInstallTime=2024-07-25 03:32:14
    lastUpdateTime=2024-07-25 03:32:14
  Package [com.example.app] (123456):
    userId=10124
    versionName=1.0.0
    firstInstallTime=2025-01-01 10:00:00
    lastUpdateTime=2025-01-02 11:00:00
"""
        parser = DumpsysPackageParser()
        result = parser.parse(sample_output)

        self.assertIn("com.android.chrome", result)
        self.assertEqual(result["com.android.chrome"]["versionName"], "83.0.4103.106")
        self.assertEqual(result["com.android.chrome"]["firstInstallTime"], "2024-07-25 03:32:14")
        self.assertEqual(result["com.android.chrome"]["lastUpdateTime"], "2024-07-25 03:32:14")

        self.assertIn("com.example.app", result)
        self.assertEqual(result["com.example.app"]["versionName"], "1.0.0")
        self.assertEqual(result["com.example.app"]["firstInstallTime"], "2025-01-01 10:00:00")
        self.assertEqual(result["com.example.app"]["lastUpdateTime"], "2025-01-02 11:00:00")

    def test_parse_empty_output(self):
        parser = DumpsysPackageParser()
        result = parser.parse("")
        self.assertEqual(result, {})

    def test_parse_partial_metadata(self):
        sample_output = """
Packages:
  Package [com.example.partial] (123):
    versionName=2.1.0
"""
        parser = DumpsysPackageParser()
        result = parser.parse(sample_output)
        self.assertIn("com.example.partial", result)
        self.assertEqual(result["com.example.partial"]["versionName"], "2.1.0")
        self.assertEqual(result["com.example.partial"]["firstInstallTime"], "UNKNOWN")
        self.assertEqual(result["com.example.partial"]["lastUpdateTime"], "UNKNOWN")
