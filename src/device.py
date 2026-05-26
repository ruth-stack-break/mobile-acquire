"""
device.py

Android device connection and metadata extraction
using adb-shell.
"""

from pathlib import Path
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


class AndroidDevice:
    """
    Handles Android device communication.
    """

    def __init__(self):
        self.device = None

    def connect(self, platform=None):
        """
        Connect to Android device/emulator with retry logic.
        """

        import time

        key_path = (
            Path.home()
            / ".android"
            / "adbkey"
        )

        signer = (
            PythonRSASigner
            .FromRSAKeyPath(
                str(key_path)
            )
        )

        attempts = 3

        if platform == "emulator":
            modes = ["tcp"]
        elif platform == "device":
            modes = ["usb"]
        else:
            modes = ["tcp", "usb"]

        for attempt in range(attempts):
            for mode in modes:
                try:
                    if mode == "tcp":
                        self.device = AdbDeviceTcp("127.0.0.1", 5555)
                    else:
                        self.device = AdbDeviceUsb()

                    self.device.connect(
                        rsa_keys=[signer],
                        auth_timeout_s=30
                    )
                    return
                except Exception as e:
                    if attempt == attempts - 1 and mode == modes[-1]:
                        raise e
            time.sleep(3)

    def shell(self, command):
        """
        Execute shell command.
        """

        return self.device.shell(command)

    def get_metadata(self):
        """
        Extract device metadata.
        """

        return {
            "model": self.shell(
                "getprop ro.product.model"
            ).strip(),

            "manufacturer": self.shell(
                "getprop ro.product.manufacturer"
            ).strip(),

            "android_version": self.shell(
                "getprop ro.build.version.release"
            ).strip(),

            "serial": self.shell(
                "getprop ro.serialno"
            ).strip(),

            "device_name": self.shell(
                "getprop ro.product.device"
            ).strip(),

            "brand": self.shell(
                "getprop ro.product.brand"
            ).strip(),

            "sdk_version": self.shell(
                "getprop ro.build.version.sdk"
            ).strip(),

            "device_time": self.shell(
                "date"
            ).strip()
        }