"""
device.py

Android device connection and metadata extraction
using adb-shell.
"""

from pathlib import Path
from adb_shell.adb_device import AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


class AndroidDevice:
    """
    Handles Android device communication.
    """

    def __init__(self):
        self.device = None

    def connect(self):
        """
        Connect to Android device using RSA auth.
        """

        key_path = Path.home() / ".android" / "adbkey"

        signer = PythonRSASigner.FromRSAKeyPath(
            str(key_path)
        )

        self.device = AdbDeviceUsb()

        self.device.connect(
        rsa_keys=[signer],
        auth_timeout_s=30
)

    def shell(self, command):
        """
        Execute shell command.
        """

        return self.device.shell(command)

    def get_metadata(self):
        """
        Get device metadata.
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
            ).strip()
        }