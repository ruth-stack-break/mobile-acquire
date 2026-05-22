import json
import tempfile
import unittest

from src.extractor import AndroidExtractor


class DummyDevice:
    def __init__(self, output):
        self.output = output

    def shell(self, command):
        return self.output


class DummyLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)


class TestAndroidExtractor(unittest.TestCase):
    def test_extract_installed_apps_handles_paths_with_equals(self):
        packages = (
            "package:/data/app/com.example=foo/base.apk=com.example\n"
            "package:/data/app/other.apk=com.other\n"
        )

        device = DummyDevice(packages)
        logger = DummyLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AndroidExtractor(device, logger)
            output_path = extractor.extract_installed_apps(tmpdir)

            with open(output_path, encoding="utf-8") as file:
                apps = json.load(file)

        self.assertEqual(len(apps), 2)
        self.assertEqual(apps[0]["apk_path"], "/data/app/com.example=foo/base.apk")
        self.assertEqual(apps[0]["package"], "com.example")
        self.assertEqual(apps[1]["apk_path"], "/data/app/other.apk")
        self.assertEqual(apps[1]["package"], "com.other")
        self.assertIn("installed_apps.json created", logger.messages)
